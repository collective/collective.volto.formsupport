# -*- coding: utf-8 -*-
from collective.volto.formsupport.interfaces import (
    ICollectiveVoltoFormsupportLayer,
)
from plone.restapi.behaviors import IBlocks
from plone.restapi.interfaces import IBlockFieldSerializationTransformer
from Products.CMFPlone.interfaces import IPloneSiteRoot
from zope.component import adapter
from zope.interface import implementer
from plone import api


class FormSerializer(object):
    """
    """

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
        current = api.user.get_current()
        if api.user.has_permission(
            "Modify portal content", user=current, obj=self.context
        ):
            return value
        return {k: v for k, v in value.items() if not k.startswith("default_")}


@implementer(IBlockFieldSerializationTransformer)
@adapter(IBlocks, ICollectiveVoltoFormsupportLayer)
class FormSerializerContents(FormSerializer):
    """ Deserializer for content-types that implements IBlocks behavior """


@implementer(IBlockFieldSerializationTransformer)
@adapter(IPloneSiteRoot, ICollectiveVoltoFormsupportLayer)
class FormSerializerRoot(FormSerializer):
    """ Deserializer for site-root """
