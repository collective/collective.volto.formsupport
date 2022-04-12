class CaptchaSupport(object):

    def __init__(self, context, request) -> None:
        self.context = context
        self.request = request

    def verify(self) -> bool:
        """
        Verify the captcha
        """
        raise NotImplementedError
