# -*- coding: utf-8 -*-

from zope.component import getUtilitiesFor, provideUtility
from zope.interface import Interface, provider
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary

try:
    from Products.validation import validation
    from Products.validation.validators.BaseValidators import baseValidators
except ImportError:  # Products.validation is optional
    validation = None
    baseValidators = None


class IFieldValidator(Interface):
    """Base marker for collective.volto.formsupport field validators."""


def _clean_validation_settings(settings):
    def delete_setting(setting):
        if hasattr(settings, setting):
            del settings[setting]

    delete_setting("name")
    delete_setting("title")
    delete_setting("description")
    delete_setting("regex_strings")
    delete_setting("regex")
    delete_setting("errmsg")
    return settings


class ValidationDefinition:
    def __init__(self, validator):
        self._name = validator.name
        self._settings = vars(validator)

    def __call__(self, value, **kwargs):
        """Allow using the class directly as a validator"""
        return self.validate(value, **kwargs)

    def settings(self):
        return self._settings

    def validate(self, value, **kwargs):
        if value is None:
            # Let the system for required take care of None values
            return
        res = validation(self._name, value, **kwargs)
        if res != 1:
            return res


def _update_validators():
    """
    Add Products.validation validators to the available list of validators
    Code taken from collective.easyform . Could lookup based on `IValidator` instead of re-registering?
    """

    if validation and baseValidators:
        for validator in baseValidators:
            provideUtility(
                ValidationDefinition(validator),
                provides=IFieldValidator,
                name=validator.name,
            )


_update_validators()


def getValidations():
    utils = getUtilitiesFor(IFieldValidator)
    return utils


@provider(IVocabularyFactory)
def ValidatorsVocabularyFactory(context, **rest):
    """Field validators vocabulary"""
    return SimpleVocabulary(
        [SimpleVocabulary.createTerm(i, i, i) for i, u in getValidations()]
    )
