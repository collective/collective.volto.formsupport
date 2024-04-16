import re

from Products.validation.interfaces.IValidator import IValidator
from zope.interface import implementer


@implementer(IValidator)
class WordsValidator:
    def __init__(
        self,
        name,
        title="",
        description="",
        words=0,
        _internal_type="",
    ):
        """ "Unused properties are for default values and type information"""
        self.name = name
        self.title = title or name
        self.description = description
        self._internal_type = _internal_type
        # Default values
        self.words = words

    def __call__(self, value="", *args, **kwargs):
        words = kwargs.get("words", self.words)
        words = int(words)
        count = len(re.findall(r"\w+", value))

        if self._internal_type == "max":
            if not value:
                return
            if count > words:
                # TODO: i18n
                msg = f"Validation failed({self.name}): is more than {words} words long"
                return msg
        elif self._internal_type == "min":
            if not value or count < words:
                # TODO: i18n
                msg = f"Validation failed({self.name}): is less than {words} words long"
                return msg
        elif self._internal_type == "test":
            pass
        else:
            # TODO: i18n
            msg = f"Validation failed({self.name}): Unknown words validator type"
            return msg
