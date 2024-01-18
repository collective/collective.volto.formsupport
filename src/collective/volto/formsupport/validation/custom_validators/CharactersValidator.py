from Products.validation.interfaces.IValidator import IValidator
from zope.interface import implementer


@implementer(IValidator)
class CharactersValidator:
    def __init__(self, name, title="", description="", characters=0, _internal_type=""):
        self.name = name
        self.title = title or name
        self.description = description
        self.characters = characters
        self._internal_type = _internal_type

    def __call__(self, value="", *args, **kwargs):
        characters = (
            int(self.characters)
            if isinstance(self.characters, str)
            else self.characters
        )
        if self._internal_type == "max":
            if not value:
                return
            if len(value) > characters:
                # TODO: i18n
                msg = f"Validation failed({self.name}): is more than {characters} characters long"
                return msg
        elif self._internal_type == "min":
            if not value or len(value) < characters:
                # TODO: i18n
                msg = f"Validation failed({self.name}): is less than {characters} characters long"
                return msg
        else:
            # TODO: i18n
            msg = f"Validation failed({self.name}): Unknown characters validator type"
            return msg
