# -*- coding: utf-8 -*-
from collective.volto.formsupport import _
from collective.volto.formsupport.interfaces import ICaptchaSupport
from collective.volto.formsupport.interfaces import IFormDataStore
from collective.volto.formsupport.interfaces import IPostEvent
from email.message import EmailMessage
from plone import api
from plone.protect.interfaces import IDisableCSRFProtection
from plone.registry.interfaces import IRegistry
from plone.restapi.deserializer import json_body
from plone.restapi.services import Service
from Products.CMFPlone.interfaces.controlpanel import IMailSchema
from zExceptions import BadRequest
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.event import notify
from zope.i18n import translate
from zope.interface import alsoProvides
from zope.interface import implementer

import codecs
import six


@implementer(IPostEvent)
class PostEventService(object):
    def __init__(self, context, data):
        self.context = context
        self.data = data


class SubmitPost(Service):
    def __init__(self, context, request):
        super(SubmitPost, self).__init__(context, request)

        self.block = {}
        self.form_data = json_body(self.request)
        self.block_id = self.form_data.get("block_id", "")
        if self.block_id:
            self.block = self.get_block_data(block_id=self.block_id)

    def reply(self):
        self.validate_form()

        store_action = self.block.get("store", False)
        send_action = self.block.get("send", False)

        # Disable CSRF protection
        alsoProvides(self.request, IDisableCSRFProtection)

        notify(PostEventService(self.context, self.form_data))

        if store_action:
            self.store_data()
        if send_action:
            self.send_data()

        return self.reply_no_content()

    def validate_form(self):
        """
        check all required fields and parameters
        """
        if not self.block_id:
            raise BadRequest(
                translate(
                    _("missing_blockid_label", default="Missing block_id"),
                    context=self.request,
                )
            )
        if not self.block:
            raise BadRequest(
                translate(
                    _(
                        "block_form_not_found_label",
                        default='Block with @type "form" and id "$block" not found in this context: $context',
                        mapping={
                            "block": self.block_id,
                            "context": self.context.absolute_url(),
                        },
                    ),
                    context=self.request,
                ),
            )

        if not self.block.get("store", False) and not self.block.get("send", False):
            raise BadRequest(
                translate(
                    _(
                        "missing_action",
                        default='You need to set at least one form action between "send" and "store".',  # noqa
                    ),
                    context=self.request,
                )
            )

        if not self.form_data.get("data", []):
            raise BadRequest(
                translate(
                    _(
                        "empty_form_data",
                        default="Empty form data.",
                    ),
                    context=self.request,
                )
            )

        if self.block.get("captcha", False):
            getMultiAdapter(
                (self.context, self.request),
                ICaptchaSupport,
                name=self.block["captcha"],
            ).verify(self.form_data.get("captcha"))

    def get_block_data(self, block_id):
        blocks = getattr(self.context, "blocks", {})
        if not blocks:
            return {}
        for id, block in blocks.items():
            if id != block_id:
                continue
            block_type = block.get("@type", "")
            if block_type != "form":
                continue
            return block
        return {}

    def get_reply_to(self):
        """This method retrieves the correct field to be used as 'reply to'.

        Three "levels" of logic:
        1. If there is a field marked with 'use_as_reply_to' set to True, that
           field wins and we use that.
           If not:
        2. We search for the "from" field.
           If not present:
        3. We use the fallback field: "default_from"
        """

        subblocks = self.block.get("subblocks", "")
        if subblocks:
            for field in subblocks:
                if field.get("use_as_reply_to", False):
                    field_id = field.get("field_id", "")
                    if field_id:
                        for data in self.form_data.get("data", ""):
                            if data.get("field_id", "") == field_id:
                                return data["value"]

        return self.form_data.get("from", "") or self.block.get("default_from", "")

    def get_bcc(self):
        bcc = []
        bcc_fields = []
        for field in self.block.get("subblocks", []):
            if field.get("use_as_bcc", False):
                field_id = field.get("field_id", "")
                if field_id not in bcc_fields:
                    bcc_fields.append(field_id)
        bcc = []
        for data in self.form_data.get("data", []):
            value = data.get("value", "")
            if not value:
                continue
            if data.get("field_id", "") in bcc_fields:
                bcc.append(data["value"])
        return bcc

    def send_data(self):
        subject = self.form_data.get("subject", "") or self.block.get(
            "default_subject", ""
        )

        mfrom = self.form_data.get("from", "") or self.block.get("default_from", "")
        mreply_to = self.get_reply_to()

        if not subject or not mfrom:
            raise BadRequest(
                translate(
                    _(
                        "send_required_field_missing",
                        default="Missing required field: subject or from.",
                    ),
                    context=self.request,
                )
            )

        portal = api.portal.get()
        overview_controlpanel = getMultiAdapter(
            (portal, self.request), name="overview-controlpanel"
        )
        if overview_controlpanel.mailhost_warning():
            raise BadRequest("MailHost is not configured.")

        registry = getUtility(IRegistry)
        mail_settings = registry.forInterface(IMailSchema, prefix="plone")
        mto = self.block.get("default_to", mail_settings.email_from_address)
        encoding = registry.get("plone.email_charset", "utf-8")
        message = self.prepare_message()

        msg = EmailMessage()
        msg.set_content(message)
        msg["Subject"] = subject
        msg["From"] = mfrom
        msg["To"] = mto
        msg["Reply-To"] = mreply_to

        msg.replace_header("Content-Type", 'text/html; charset="utf-8"')

        self.manage_attachments(msg=msg)

        self.send_mail(msg=msg, encoding=encoding)

        for bcc in self.get_bcc():
            # send a copy also to the fields with bcc flag
            msg.replace_header("To", bcc)
            self.send_mail(msg=msg, encoding=encoding)

    def prepare_message(self):
        message_template = api.content.get_view(
            name="send_mail_template",
            context=self.context,
            request=self.request,
        )
        parameters = {
            "parameters": self.filter_parameters(),
            "url": self.context.absolute_url(),
            "title": self.context.Title(),
        }
        return message_template(**parameters)

    def filter_parameters(self):
        """
        do not send attachments fields.
        """
        skip_fields = [
            x.get("field_id", "")
            for x in self.block.get("subblocks", [])
            if x.get("field_type", "") == "attachment"
        ]
        return [
            x
            for x in self.form_data.get("data", [])
            if x.get("field_id", "") not in skip_fields
        ]

    def send_mail(self, msg, encoding):
        host = api.portal.get_tool(name="MailHost")
        host.send(msg, charset=encoding)

    def manage_attachments(self, msg):
        attachments = self.form_data.get("attachments", {})
        if not attachments:
            return []
        for key, value in attachments.items():
            content_type = "application/octet-stream"
            filename = None
            if isinstance(value, dict):
                file_data = value.get("data", "")
                if not file_data:
                    continue
                content_type = value.get("content-type", content_type)
                filename = value.get("filename", filename)
                if isinstance(file_data, six.text_type):
                    file_data = file_data.encode("utf-8")
                if "encoding" in value:
                    file_data = codecs.decode(file_data, value["encoding"])
                if isinstance(file_data, six.text_type):
                    file_data = file_data.encode("utf-8")
            else:
                file_data = value
            msg.add_attachment(
                file_data,
                maintype=content_type,
                subtype=content_type,
                filename=filename,
            )

    def store_data(self):
        store = getMultiAdapter((self.context, self.request), IFormDataStore)
        res = store.add(data=self.filter_parameters())
        if not res:
            raise BadRequest("Unable to store data")
