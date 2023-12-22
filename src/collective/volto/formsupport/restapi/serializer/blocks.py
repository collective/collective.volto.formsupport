# -*- coding: utf-8 -*-
from collective.volto.formsupport.interfaces import ICaptchaSupport
from collective.volto.formsupport.interfaces import ICollectiveVoltoFormsupportLayer
from plone import api
from plone.restapi.behaviors import IBlocks
from plone.restapi.interfaces import IBlockFieldSerializationTransformer
from Products.CMFPlone.interfaces import IPloneSiteRoot
from zope.component import adapter
from zope.component import getMultiAdapter
from zope.interface import implementer

import os


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

        for field in value.get("subblocks", []):
            if field.get('validationSettings'):
                self._update_validations(field)

        if api.user.has_permission("Modify portal content", obj=self.context):
            return value
        return {k: v for k, v in value.items() if not k.startswith("default_")}

    def _update_validations(self, field):
        validations = field.get("validations")
        new_settings = field.get('validationSettings')
        # The settings were collapsed on the frontend, we need to find the validation it was for
        for validation_id in validations:
            settings = {
                setting_name: val
                for setting_name, val in new_settings.items()
                if setting_name not in IGNORED_VALIDATION_DEFINITION_ARGUMENTS
            } if field.get(validation_id) else None
            # breakpoint()
            if settings:
                field[validation_id] = settings
                    


@implementer(IBlockFieldSerializationTransformer)
@adapter(IBlocks, ICollectiveVoltoFormsupportLayer)
class FormSerializerContents(FormSerializer):
    """Deserializer for content-types that implements IBlocks behavior"""


@implementer(IBlockFieldSerializationTransformer)
@adapter(IPloneSiteRoot, ICollectiveVoltoFormsupportLayer)
class FormSerializerRoot(FormSerializer):
    """Deserializer for site-root"""
