from . import CaptchaSupport
from collective.honeypot.config import HONEYPOT_FIELD
from collective.honeypot.utils import found_honeypot
from collective.volto.formsupport import _
from plone.restapi.deserializer import json_body
from zExceptions import BadRequest
from zope.i18n import translate


class HoneypotSupport(CaptchaSupport):
    name = _("Honeypot Support")

    def isEnabled(self):
        """
        Honeypot is enabled with env vars
        """
        return True

    def serialize(self):
        if not HONEYPOT_FIELD:
            # no field is set, so we only want to log.
            return {}

        return {"id": HONEYPOT_FIELD}

    def verify(self, data):
        form_data = json_body(self.request).get("data", [])
        form = {x["label"]: x["value"] for x in form_data}
        if found_honeypot(form, required=True):
            raise BadRequest(
                translate(
                    _("honeypot_error", default="Error submitting form."),
                    context=self.request,
                )
            )
