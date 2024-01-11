# -*- coding: utf-8 -*-


import codecs
import logging
import math
import os
from datetime import datetime
from email.message import EmailMessage
from xml.etree.ElementTree import Element, ElementTree, SubElement

import six
from plone import api
from plone.protect.interfaces import IDisableCSRFProtection
from plone.registry.interfaces import IRegistry
from plone.restapi.deserializer import json_body
from plone.restapi.services import Service
from Products.CMFPlone.interfaces.controlpanel import IMailSchema
from zExceptions import BadRequest
from zope.component import getMultiAdapter, getUtility
from zope.event import notify
from zope.i18n import translate
from zope.interface import alsoProvides, implementer

from collective.volto.formsupport import _
from collective.volto.formsupport.interfaces import (
    ICaptchaSupport,
    IFormDataStore,
    IPostEvent,
)
from collective.volto.formsupport.restapi.services.submit_form.field import (
    construct_fields,
)
from collective.volto.formsupport.utils import get_blocks

logger = logging.getLogger(__name__)
CTE = os.environ.get("MAIL_CONTENT_TRANSFER_ENCODING", None)


@implementer(IPostEvent)
class PostEventService(object):
    def __init__(self, context, data):
        self.context = context
        self.data = data


class SubmitPost(Service):
    fields = []

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
        send_action = self.block.get("send", [])

        # Disable CSRF protection
        alsoProvides(self.request, IDisableCSRFProtection)

        notify(PostEventService(self.context, self.form_data))

        # Construct self.fieldss
        fields_data = []
        for submitted_field in self.form_data.get("data", []):
            # TODO: Review if fields submitted without a field_id should be included. Is breaking change if we remove it
            if submitted_field.get("field_id") is None:
                fields_data.append(submitted_field)
                continue
            for field in self.block.get("subblocks", []):
                if field.get("id", field.get("field_id")) == submitted_field.get(
                    "field_id"
                ):
                    fields_data.append(
                        {
                            **field,
                            **submitted_field,
                            "display_value_mapping": field.get("display_values"),
                            "custom_field_id": self.block.get(field["field_id"]),
                        }
                    )
        self.fields = construct_fields(fields_data)

        if send_action:
            try:
                self.send_data()
            except BadRequest as e:
                raise e
            except Exception as e:
                logger.exception(e)
                message = translate(
                    _(
                        "mail_send_exception",
                        default="Unable to send confirm email. Please retry later or contact site administator.",
                    ),
                    context=self.request,
                )
                self.request.response.setStatus(500)
                return dict(type="InternalServerError", message=message)
        if store_action:
            self.store_data()

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

        if not self.block.get("store", False) and not self.block.get("send", []):
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

        self.validate_attachments()
        if self.block.get("captcha", False):
            getMultiAdapter(
                (self.context, self.request),
                ICaptchaSupport,
                name=self.block["captcha"],
            ).verify(self.form_data.get("captcha"))

    def validate_attachments(self):
        attachments_limit = os.environ.get("FORM_ATTACHMENTS_LIMIT", "")
        if not attachments_limit:
            return
        attachments = self.form_data.get("attachments", {})
        attachments_len = 0
        for attachment in attachments.values():
            data = attachment.get("data", "")
            attachments_len += (len(data) * 3) / 4 - data.count("=", -2)
        if attachments_len > float(attachments_limit) * pow(1024, 2):
            size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
            i = int(math.floor(math.log(attachments_len, 1024)))
            p = math.pow(1024, i)
            s = round(attachments_len / p, 2)
            uploaded_str = "{} {}".format(s, size_name[i])
            raise BadRequest(
                translate(
                    _(
                        "attachments_too_big",
                        default="Attachments too big. You uploaded ${uploaded_str},"
                        " but limit is ${max} MB. Try to compress files.",
                        mapping={
                            "max": attachments_limit,
                            "uploaded_str": uploaded_str,
                        },
                    ),
                    context=self.request,
                )
            )

    def get_block_data(self, block_id):
        blocks = get_blocks(self.context)
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
                                return data.get("value", "")

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

    def get_acknowledgement_field_value(self):
        acknowledgementField = self.block["acknowledgementFields"]
        for field in self.block.get("subblocks", []):
            if field.get("field_id") == acknowledgementField:
                for data in self.form_data.get("data", []):
                    if data.get("field_id", "") == field.get("field_id"):
                        return data.get("value")

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
        charset = registry.get("plone.email_charset", "utf-8")

        should_send = self.block.get("send", [])
        if should_send:
            mto = self.block.get("default_to", mail_settings.email_from_address)
            message = self.prepare_message()

            msg = EmailMessage()
            msg.set_content(message, charset=charset, subtype="html", cte=CTE)
            msg["Subject"] = subject
            msg["From"] = mfrom
            msg["To"] = mto
            msg["Reply-To"] = mreply_to
            msg.replace_header("Content-Type", 'text/html; charset="utf-8"')

            headers_to_forward = self.block.get("httpHeaders", [])
            for header in headers_to_forward:
                header_value = self.request.get(header)
                if header_value:
                    msg[header] = header_value

            self.manage_attachments(msg=msg)

            if isinstance(should_send, list):
                if "recipient" in self.block.get("send", []):
                    self.send_mail(msg=msg, charset=charset)
                # Backwards compatibility for forms before 'acknowledgement' sending
            else:
                self.send_mail(msg=msg, charset=charset)

            # send a copy also to the fields with bcc flag
            for bcc in self.get_bcc():
                msg.replace_header("To", bcc)
                self.send_mail(msg=msg, charset=charset)

        acknowledgement_message = self.block.get("acknowledgementMessage")
        if acknowledgement_message and "acknowledgement" in self.block.get("send", []):
            acknowledgement_address = self.get_acknowledgement_field_value()
            if acknowledgement_address:
                acknowledgement_mail = EmailMessage()
                acknowledgement_mail["Subject"] = subject
                acknowledgement_mail["From"] = mfrom
                acknowledgement_mail["To"] = acknowledgement_address
                acknowledgement_mail.set_content(
                    acknowledgement_message.get("data"), subtype="html", charset="utf-8"
                )
                self.send_mail(msg=acknowledgement_mail, charset=charset)

    def prepare_message(self):
        email_format_page_template_mapping = {
            "list": "send_mail_template",
            "table": "send_mail_template_table",
        }
        email_format = self.block.get("email_format", "")
        template_name = email_format_page_template_mapping.get(
            email_format, "send_mail_template"
        )

        message_template = api.content.get_view(
            name=template_name,
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
        return [field for field in self.fields if field.send_in_email]

    def send_mail(self, msg, charset):
        host = api.portal.get_tool(name="MailHost")
        # we set immediate=True because we need to catch exceptions.
        # by default (False) exceptions are handled by MailHost and we can't catch them.
        host.send(msg, charset=charset, immediate=True)

    def manage_attachments(self, msg):
        attachments = self.form_data.get("attachments", {})

        if self.block.get("attachXml", False):
            self.attach_xml(msg=msg)

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
            maintype, subtype = content_type.split("/")
            msg.add_attachment(
                file_data,
                maintype=maintype,
                subtype=subtype,
                filename=filename,
            )

    def attach_xml(self, msg):
        now = (
            datetime.now()
            .isoformat(timespec="seconds")
            .replace(" ", "-")
            .replace(":", "")
        )
        filename = f"formdata_{now}.xml"
        output = six.BytesIO()
        xmlRoot = Element("form")

        for field in self.filter_parameters():
            SubElement(xmlRoot, "field", name=field.field_id).text = str(field._value)

        doc = ElementTree(xmlRoot)
        doc.write(output, encoding="utf-8", xml_declaration=True)
        xmlstr = output.getvalue()
        msg.add_attachment(
            xmlstr,
            maintype="application",
            subtype="xml",
            filename=filename,
        )

    def store_data(self):
        store = getMultiAdapter((self.context, self.request), IFormDataStore)
        res = store.add(data=self.filter_parameters())
        if not res:
            raise BadRequest("Unable to store data")
