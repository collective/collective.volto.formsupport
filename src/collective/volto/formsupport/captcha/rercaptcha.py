from collective.rercaptcha.eventsubscribers import is_captcha_enabled
from collective.rercaptcha.eventsubscribers import is_valid_rercaptcha
from collective.volto.formsupport import _
from collective.volto.formsupport.captcha import CaptchaSupport
from zExceptions import BadRequest
from zope.i18n import translate


class RercaptchaSupport(CaptchaSupport):
    name = _("Rercaptcha Support")

    def isEnabled(self):
        """
        Rercaptcha is enabled with registry vars
        """
        return is_captcha_enabled()

    def verify(self, data):

        if not is_valid_rercaptcha(data):
            raise BadRequest(
                translate(
                    _("The code you entered was wrong, please enter the new one."),
                    context=self.request,
                )
            )
