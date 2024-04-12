# -*- coding: utf-8 -*-

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parseaddr

from plone import api
from plone.restapi.deserializer import json_body
from plone.restapi.services import Service
from zExceptions import BadRequest

from collective.volto.formsupport import _
from collective.volto.formsupport.utils import (
    generate_email_token,
    validate_email_token,
)

logger = logging.getLogger(__name__)


class ValidateEmailMessage(Service):
    def reply(self):
        data = data = self.validate()

        self.send_token(generate_email_token(data["uid"], data["email"]), data["email"])

        return self.reply_no_content()

    def send_token(self, token, email):
        """
        Send token to recipient
        """

        mail_view = api.content.get_view(
            context=api.portal.get(), name="email-confirm-view"
        )
        content = mail_view(token=token)
        mfrom = api.portal.get_registry_record("plone.email_from_address")

        host = api.portal.get_tool("MailHost")
        msg = MIMEMultipart()
        msg.attach(MIMEText(content, "html"))
        msg["Subject"] = _("Email confirmation code")
        msg["From"] = mfrom
        msg["To"] = email

        try:
            host.send(msg, charset="utf-8")
        except Exception as e:
            logger.error(f"The email confirmation message was not send due to {e}")

    def validate(self):
        data = json_body(self.request)

        if "email" not in data:
            raise BadRequest(_("The email field is missing"))

        if "@" not in parseaddr(data["email"])[1]:
            raise BadRequest(_("The provided email address is not valid"))

        if "uid" not in data:
            raise BadRequest(_("The uid field is missing"))

        return data


class ValidateEmailToken(Service):
    def reply(self):
        self.validate()

        return self.reply_no_content()

    def validate(self):
        data = json_body(self.request)

        if "email" not in data:
            raise BadRequest(_("The email field is missing"))

        if "otp" not in data:
            raise BadRequest(_("The otp field is missing"))

        if "uid" not in data:
            raise BadRequest(_("The uid field is missing"))

        if not validate_email_token(data["uid"], data["email"], data["otp"]):
            raise BadRequest(_("OTP is wrong"))
