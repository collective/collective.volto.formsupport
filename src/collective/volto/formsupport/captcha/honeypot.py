from . import CaptchaSupport
from collective.honeypot.config import EXTRA_PROTECTED_ACTIONS
from collective.honeypot.config import HONEYPOT_FIELD
from collective.honeypot.utils import check_post
from collective.volto.formsupport import _


class HoneypotSupport(CaptchaSupport):
    name = _("Honeypot Support")

    def isEnabled(self):
        """
        Honeypot is enabled with env vars
        """
        return "submit-form" in EXTRA_PROTECTED_ACTIONS

    def serialize(self):
        if not HONEYPOT_FIELD:
            # no field is set, so we only want to log.
            return {}

        return {"id": HONEYPOT_FIELD}

    def verify(self, data):
        check_post()
