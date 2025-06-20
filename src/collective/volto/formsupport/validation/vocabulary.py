# -*- coding: utf-8 -*-

from zope.interface import  provider
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary

from collective.volto.formsupport.validation import getValidations


@provider(IVocabularyFactory)
def ValidatorsVocabularyFactory(context, **rest):
    """Field validators vocabulary"""
    breakpoint()

    return SimpleVocabulary(
        [SimpleVocabulary.createTerm(i, i, i) for i, u in getValidations()]
    )
