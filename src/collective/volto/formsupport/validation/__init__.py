# -*- coding: utf-8 -*-

from zope.component import getUtilitiesFor, provideUtility
from zope.interface import Interface, provider
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary

from collective.volto.formsupport.validation.custom_validators import custom_validators
from collective.volto.formsupport.validation.definition import ValidationDefinition

try:
    from Products.validation.validators.BaseValidators import baseValidators
except ImportError:  # Products.validation is optional
    validation = None
    baseValidators = None


IGNORED_VALIDATION_DEFINITION_ARGUMENTS = [
    "title",
    "description",
    "name",
    "errmsg",
    "regex",
    "regex_strings",
    "ignore",
    "_internal_type",
]


class IFieldValidator(Interface):
    """Base marker for collective.volto.formsupport field validators."""


def _update_validators():
    """
    Add Products.validation validators to the available list of validators
    Code taken from collective.easyform . Could lookup based on `IValidator` instead of re-registering?
    """

    if baseValidators:
        for validator in baseValidators:
            provideUtility(
                ValidationDefinition(validator),
                provides=IFieldValidator,
                name=validator.name,
            )
    for validator in custom_validators:
        provideUtility(
            ValidationDefinition(validator),
            provides=IFieldValidator,
            name=validator.name,
        )


_update_validators()


def getValidations():
    utils = getUtilitiesFor(IFieldValidator)
    return utils


PYTHON_TYPE_SCHEMA_TYPE_MAPPING = {
    "bool": "boolean",
    "date": "date",
    "dict": "obj",
    "float": "number",
    "int": "integer",
    "list": "array",
    "str": "string",
    "time": "datetime",
}


def get_validation_information():
    """Adds the individual validation settings to the `validationSettings` key in the format `{validation_id}-{setting_name}`"""
    settings_to_add = {}

    for validation_id, validation in getValidations():
        settings = validation.settings
        if not isinstance(settings, dict) or not settings:
            # We don't have any settings, skip including it
            continue
        cleaned_settings = {
            setting_name: val
            for setting_name, val in settings.items()
            if setting_name not in IGNORED_VALIDATION_DEFINITION_ARGUMENTS
        }

        for setting_id, setting_value in cleaned_settings.items():
            settings_to_add[f"{validation_id}-{setting_id}"] = {
                "validation_title": getattr(settings, "title", validation_id),
                "title": setting_id,
                "type": PYTHON_TYPE_SCHEMA_TYPE_MAPPING.get(
                    type(setting_value).__name__, "string"
                ),
                "default": setting_value,
            }

    return settings_to_add


@provider(IVocabularyFactory)
def ValidatorsVocabularyFactory(context, **rest):
    """Field validators vocabulary"""
    return SimpleVocabulary(
        [SimpleVocabulary.createTerm(i, i, i) for i, u in getValidations()]
    )
