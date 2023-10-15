class CaptchaSupport(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def isEnabled(self):
        return True

    def verify(self):
        """
        Verify the captcha
        """
        raise NotImplementedError
