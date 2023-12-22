from Products.validation.interfaces.IValidator import IValidator
from zope.interface import implementer

from collective.volto.formsupport.validation import ValidationDefinition


# TODO: Tidy up code structure so we don't need to be a definition
@implementer(IValidator)
class CharactersValidator(ValidationDefinition):
    def __init__(self, name, title="", description="", characters=0, _internal_type=""):
        self.name = name
        self.title = title or name
        self.description = description
        self.characters = characters
        self._internal_type = _internal_type

        # From super class. Hacky implementation having this here for now
        self._name = name
        # self._name = name
        # self.settings = vars(self)

    @property
    def settings(self):
        return vars(self)

    def __call__(self, value="", *args, **kwargs):
        if self._internal_type == "max":
            if (not value or len(value) > self.characters):
                # TODO: i18n
                msg = f"Validation failed({self.name}): is more than {self.characters}"
                return msg
        elif self._internal_type == "min":
            if (not value or len(value) < self.characters):
                # TODO: i18n
                msg = f"Validation failed({self.name}): is less than {self.characters}",
                return msg
        else:
            # TODO: i18n
            msg = f"Validation failed({self.name}): Unknown characters validator type",
            return msg


