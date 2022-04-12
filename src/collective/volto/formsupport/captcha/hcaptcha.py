from . import CaptchaSupport
from plone.formwidget.hcaptcha.interfaces import IHCaptchaSettings
from plone.formwidget.hcaptcha.nohcaptcha import submit
from plone.formwidget.hcaptcha.validator import WrongCaptchaCode
from plone.registry.interfaces import IRegistry
from zope.component import queryUtility


class HCaptchaSupport(CaptchaSupport):
    def __init__(self, context, request):
        super().__init__(context, request)
        registry = queryUtility(IRegistry)
        self.settings = registry.forInterface(IHCaptchaSettings)

    def verify(self, data) -> bool:
        if not self.settings.private_key:
            raise ValueError(
                "No hcaptcha private key configured. Go to "
                "path/to/site/@@hcaptcha-settings to configure."
            )
        token = data["token"]
        remote_addr = self.request.get("HTTP_X_FORWARDED_FOR", "").split(",")[0]
        if not remote_addr:
            remote_addr = self.request.get("REMOTE_ADDR")
        res = submit(token, self.settings.private_key, remote_addr)
        if not res.is_valid:
            raise WrongCaptchaCode
