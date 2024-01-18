# -*- coding: utf-8 -*-
import os

from plone import api
from plone.restapi.behaviors import IBlocks
from plone.restapi.interfaces import IBlockFieldSerializationTransformer
from Products.CMFPlone.interfaces import IPloneSiteRoot
from zope.component import adapter, getMultiAdapter
from zope.interface import implementer

from collective.volto.formsupport.interfaces import (
    ICaptchaSupport,
    ICollectiveVoltoFormsupportLayer,
)

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
        """Adds the individual validation settings to the `validationSettings` key in the format `{validation_id}-{setting_name}`"""
        validation_settings = field.get("validationSettings")
        settings_to_add = {}
        for validation_id, settings in validation_settings.items():
            if not isinstance(settings, dict):
                continue
            cleaned_settings = {
                f"{validation_id}-{setting_name}": val
                for setting_name, val in settings.items()
                if setting_name not in IGNORED_VALIDATION_DEFINITION_ARGUMENTS
            }

            if cleaned_settings:
                settings_to_add = {**settings_to_add, **cleaned_settings}
        field["validationSettings"] = {**validation_settings, **settings_to_add}

        return field


@implementer(IBlockFieldSerializationTransformer)
@adapter(IBlocks, ICollectiveVoltoFormsupportLayer)
class FormSerializerContents(FormSerializer):
    """Deserializer for content-types that implements IBlocks behavior"""


@implementer(IBlockFieldSerializationTransformer)
@adapter(IPloneSiteRoot, ICollectiveVoltoFormsupportLayer)
class FormSerializerRoot(FormSerializer):
    """Deserializer for site-root"""
