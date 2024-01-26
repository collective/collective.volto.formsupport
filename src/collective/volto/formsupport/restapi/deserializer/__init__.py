from plone.base.interfaces import IPloneSiteRoot
from plone.restapi.behaviors import IBlocks
from plone.restapi.interfaces import IBlockFieldDeserializationTransformer
from zope.component import adapter
from zope.interface import implementer
from zope.publisher.interfaces.browser import IBrowserRequest


@adapter(IBlocks, IBrowserRequest)
class FormBlockDeserializerBase:
    block_type = "form"
    order = 100

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, block):
        return self._process_data(block)

    def _process_data(
        self,
        data,
    ):
        self._update_validations(data)
        return data

    def _update_validations(self, data):
        for field in data.get("subblocks"):
            if field.get("field_type") not in ["text", "textarea", "from"]:
                field["validations"] = []
                field["validationSettings"] = {}


@implementer(IBlockFieldDeserializationTransformer)
@adapter(IBlocks, IBrowserRequest)
class FormBlockDeserializer(FormBlockDeserializerBase):
    """Serializer for content-types with IBlocks behavior"""


@implementer(IBlockFieldDeserializationTransformer)
@adapter(IPloneSiteRoot, IBrowserRequest)
class FormBlockDeserializerRoot(FormBlockDeserializerBase):
    """Serializer for site root"""
