from bs4 import BeautifulSoup
from datetime import datetime
from email import policy
from email.message import EmailMessage
from io import BytesIO
from plone import api

import codecs
import logging
import os
import re


try:
    from plone.base.interfaces.controlpanel import IMailSchema
except ImportError:
    from Products.CMFPlone.interfaces.controlpanel import IMailSchema

from collective.volto.formsupport import _
from collective.volto.formsupport.events import FormSubmittedEvent
from collective.volto.formsupport.interfaces import IFormDataStore
from collective.volto.formsupport.interfaces import IPostAdapter
from collective.volto.formsupport.interfaces import IPostEvent
from collective.volto.formsupport.utils import get_blocks
from plone.protect.interfaces import IDisableCSRFProtection
from plone.registry.interfaces import IRegistry
from plone.restapi.services import Service
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import SubElement
from zExceptions import BadRequest
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.event import notify
from zope.i18n import translate
from zope.interface import alsoProvides
from zope.interface import implementer


logger = logging.getLogger(__name__)
CTE = os.environ.get("MAIL_CONTENT_TRANSFER_ENCODING", None)


@implementer(IPostEvent)
class PostEventService:
    def __init__(self, context, data):
        self.context = context
        self.data = data


class SubmitPost(Service):
    def __init__(self, context, request):
        super().__init__(context, request)

        self.block = {}
        self.form_data_adapter = getMultiAdapter(
            (self.context, self.request), IPostAdapter
        )
        self.form_data = self.get_form_data()
        self.block_id = self.form_data.get("block_id", "")

        if self.block_id:
            self.block = self.get_block_data(block_id=self.block_id)

    def reply(self):
        store_action = self.block.get("store", False)
        send_action = self.block.get("send", [])

        # Disable CSRF protection
        alsoProvides(self.request, IDisableCSRFProtection)

        notify(PostEventService(self.context, self.form_data))

        if send_action or self.get_bcc():
            try:
                self.send_data()
            except BadRequest as e:
                raise e
            except Exception as e:
                logger.exception(e)
                message = translate(
                    _(
                        "mail_send_exception",
                        default="Unable to send confirm email. Please retry later or contact site administrator.",
                    ),
                    context=self.request,
                )
                self.request.response.setStatus(500)
                return dict(type="InternalServerError", message=message)

        notify(FormSubmittedEvent(self.context, self.block, self.form_data))

        if store_action:
            self.store_data()

        return {"data": self.form_data.get("data", [])}

    def get_form_data(self):
        return self.form_data_adapter()

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

    def get_subject(self):
        subject = self.form_data.get("subject", "") or self.block.get(
            "default_subject", ""
        )

        for i in self.form_data.get("data", []):

            field_id = i.get("field_id")

            if not field_id:
                continue

            # Handle this kind of id format: `field_name_123321, whichj is used by frontend package logics
            pattern = r"\$\{[^}]+\}"
            matches = re.findall(pattern, subject)

            for match in matches:
                if field_id in match:
                    subject = subject.replace(match, str(i.get("value")))

        return subject

    def send_data(self):

        subject = self.get_subject()

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
        bcc = self.get_bcc()

        if should_send or bcc:
            portal_transforms = api.portal.get_tool(name="portal_transforms")
            mto = self.block.get("default_to", mail_settings.email_from_address)
            message = self.prepare_message()
            text_message = (
                portal_transforms.convertTo("text/plain", message, mimetype="text/html")
                .getData()
                .strip()
            )
            msg = EmailMessage(policy=policy.SMTP)
            msg.set_content(text_message, cte=CTE)
            msg.add_alternative(message, subtype="html", cte=CTE)
            msg["Subject"] = subject
            msg["From"] = mfrom
            msg["To"] = mto
            msg["Reply-To"] = mreply_to

            headers_to_forward = self.block.get("httpHeaders", [])
            for header in headers_to_forward:
                header_value = self.request.get(header)
                if header_value:
                    msg[header] = header_value

            self.manage_attachments(msg=msg)

            if should_send and isinstance(should_send, list):
                if "recipient" in self.block.get("send", []):
                    self.send_mail(msg=msg, charset=charset)
                # Backwards compatibility for forms before 'acknowledgement' sending
            elif should_send:
                self.send_mail(msg=msg, charset=charset)

            # send a copy also to the fields with bcc flag
            for bcc in self.get_bcc():
                msg.replace_header("To", bcc)
                self.send_mail(msg=msg, charset=charset)

        acknowledgement_message = self.block.get("acknowledgementMessage")
        if acknowledgement_message and "acknowledgement" in self.block.get("send", []):
            acknowledgement_address = self.get_acknowledgement_field_value()
            if acknowledgement_address:
                acknowledgement_mail = EmailMessage(policy=policy.SMTP)
                acknowledgement_mail["Subject"] = subject
                acknowledgement_mail["From"] = mfrom
                acknowledgement_mail["To"] = acknowledgement_address
                ack_msg = acknowledgement_message.get("data")
                ack_msg_text = (
                    portal_transforms.convertTo(
                        "text/plain", ack_msg, mimetype="text/html"
                    )
                    .getData()
                    .strip()
                )
                acknowledgement_mail.set_content(ack_msg_text, cte=CTE)
                acknowledgement_mail.add_alternative(ack_msg, subtype="html", cte=CTE)
                self.send_mail(msg=acknowledgement_mail, charset=charset)

    def prepare_message(self):

        mail_header = self.block.get("mail_header", {}).get("data", "")
        mail_footer = self.block.get("mail_footer", {}).get("data", "")

        # Check if there is content
        bs_mail_header = BeautifulSoup(mail_header)
        bs_mail_footer = BeautifulSoup(mail_footer)

        portal = getMultiAdapter(
            (self.context, self.request), name="plone_portal_state"
        ).portal()

        frontend_domain = api.portal.get_registry_record(
            name="volto.frontend_domain", default=""
        )

        for snippet in [bs_mail_header, bs_mail_footer]:
            if snippet:
                for link in snippet.find_all("a"):
                    if link.get("href", "").startswith("/"):
                        link["href"] = (
                            frontend_domain or portal.absolute_url()
                        ) + link["href"]

        mail_header = bs_mail_header.get_text() and bs_mail_header.prettify() or None
        mail_footer = bs_mail_footer.get_text() and bs_mail_footer.prettify() or None

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
            "parameters": self.form_data_adapter.format_fields(),
            "url": self.context.absolute_url(),
            "title": self.context.Title(),
            "mail_header": mail_header,
            "mail_footer": mail_footer,
        }
        return message_template(**parameters)

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
                if isinstance(file_data, str):
                    file_data = file_data.encode("utf-8")
                if "encoding" in value:
                    file_data = codecs.decode(file_data, value["encoding"])
                if isinstance(file_data, str):
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
        output = BytesIO()
        xmlRoot = Element("form")

        for field in self.form_data_adapter.filter_parameters():
            SubElement(
                xmlRoot, "field", name=field.get("custom_field_id", field["label"])
            ).text = str(field.get("value", ""))

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

        res = store.add(data=self.form_data_adapter.filter_parameters())

        if not res:
            raise BadRequest("Unable to store data")
