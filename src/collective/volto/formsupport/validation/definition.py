from Products.validation import validation


class ValidationDefinition:
    def __init__(self, validator):
        self._name = validator.name
        self._settings = vars(validator)

    def __call__(self, value, **kwargs):
        """Allow using the class directly as a validator"""
        return self.validate(value, **kwargs)

    @property
    def settings(self):
        return self._settings

    @settings.setter
    def settings(self, value):
        self._value = value

    def validate(self, value, **kwargs):
        if value is None:
            # Let the system for required take care of None values
            return
        res = validation(self._name, value, **kwargs)
        if res != 1:
            return res
