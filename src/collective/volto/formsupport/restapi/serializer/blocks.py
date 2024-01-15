# -*- coding: utf-8 -*-
import os

from plone import api
from plone.restapi.behaviors import IBlocks
from plone.restapi.interfaces import IBlockFieldSerializationTransformer
from plone.restapi.serializer.converters import json_compatible
from Products.CMFPlone.interfaces import IPloneSiteRoot
from zope.component import adapter, getMultiAdapter
from zope.interface import implementer

from collective.volto.formsupport.interfaces import (
    ICaptchaSupport,
    ICollectiveVoltoFormsupportLayer,
)
from collective.volto.formsupport.validation import getValidations

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


class FormSerializer(object):
    """ """

    order = 200  # after standard ones
    block_type = "form"

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, value):
        """
        If user can edit the context, return the full block data.
        Otherwise, skip default values because we need them only in edit and
        to send emails from the backend.
        """
        if "captcha" in value and value["captcha"]:
            value["captcha_props"] = getMultiAdapter(
                (self.context, self.request),
                ICaptchaSupport,
                name=value["captcha"],
            ).serialize()
        attachments_limit = os.environ.get("FORM_ATTACHMENTS_LIMIT", "")
        if attachments_limit:
            value["attachments_limit"] = attachments_limit

        for index, field in enumerate(value.get("subblocks", [])):
            if field.get("validationSettings"):
                value["subblocks"][index] = self._expand_validation_field(field)

        if api.user.has_permission("Modify portal content", obj=self.context):
            return value
        return {k: v for k, v in value.items() if not k.startswith("default_")}

    def _expand_validation_field(self, field):
        field_validations = field.get("validations")
        matched_validation_definitions = [
            validation
            for validation in getValidations()
            if validation[0] in field_validations
        ]

        for validation_id, validation in matched_validation_definitions:
            settings = validation.settings
            settings = {
                setting_name: val
                for setting_name, val in settings.items()
                if setting_name not in IGNORED_VALIDATION_DEFINITION_ARGUMENTS
            }
            if settings:
                field[validation_id] = json_compatible(settings)

        return field


@implementer(IBlockFieldSerializationTransformer)
@adapter(IBlocks, ICollectiveVoltoFormsupportLayer)
class FormSerializerContents(FormSerializer):
    """Deserializer for content-types that implements IBlocks behavior"""


@implementer(IBlockFieldSerializationTransformer)
@adapter(IPloneSiteRoot, ICollectiveVoltoFormsupportLayer)
class FormSerializerRoot(FormSerializer):
    """Deserializer for site-root"""
