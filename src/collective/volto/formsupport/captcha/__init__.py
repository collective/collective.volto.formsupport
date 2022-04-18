class CaptchaSupport(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def verify(self):
        """
        Verify the captcha
        """
        raise NotImplementedError
