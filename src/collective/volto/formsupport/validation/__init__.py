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


@provider(IVocabularyFactory)
def ValidatorsVocabularyFactory(context, **rest):
    """Field validators vocabulary"""
    return SimpleVocabulary(
        [SimpleVocabulary.createTerm(i, i, i) for i, u in getValidations()]
    )
