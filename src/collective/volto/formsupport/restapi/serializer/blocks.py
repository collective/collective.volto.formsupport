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
from collective.volto.formsupport.validation import get_validation_information


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

        # Add information on the settings for validations to the response
        validation_settings = get_validation_information()
        value["validationSettings"] = validation_settings

        if api.user.has_permission("Modify portal content", obj=self.context):
            return value
        return {k: v for k, v in value.items() if not k.startswith("default_")}


@implementer(IBlockFieldSerializationTransformer)
@adapter(IBlocks, ICollectiveVoltoFormsupportLayer)
class FormSerializerContents(FormSerializer):
    """Deserializer for content-types that implements IBlocks behavior"""


@implementer(IBlockFieldSerializationTransformer)
@adapter(IPloneSiteRoot, ICollectiveVoltoFormsupportLayer)
class FormSerializerRoot(FormSerializer):
    """Deserializer for site-root"""
