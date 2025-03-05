from plone.api.portal import get_registry_record
from plone.api.portal import set_registry_record
from plone.dexterity.interfaces import IDexterityContent
from plone.restapi.bbb import IPloneSiteRoot
from plone.restapi.interfaces import IBlockFieldDeserializationTransformer
from Products.PortalTransforms.transforms.safe_html import SafeHTML
from uuid import uuid4
from zope.component import adapter
from zope.interface import implementer
from zope.publisher.interfaces.browser import IBrowserRequest


GLOBAL_FORM_REGISTRY_RECORD_ID = (
    "collective.volto.formsupport.interfaces.IGlobalFormStore.global_forms_config"
)


def update_global_forms(value):
    global_form_id = value.get("global_form_id")

    if not global_form_id:
        global_form_id = str(uuid4())

    global_forms_record = get_registry_record(GLOBAL_FORM_REGISTRY_RECORD_ID)
    global_forms_record[global_form_id] = value
    set_registry_record(GLOBAL_FORM_REGISTRY_RECORD_ID, global_forms_record)

    value["global_form_id"] = global_form_id
    return value


class FormBlockDeserializerBase:
    """FormBlockDeserializerBase."""

    order = 100

    block_type = "form"

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, value):
        """
        Do not store html but only plaintext
        """
        if value.get("send_message", ""):
            transform = SafeHTML()
            value["send_message"] = transform.scrub_html(value["send_message"])
        value = update_global_forms(value)
        return value


@adapter(IDexterityContent, IBrowserRequest)
@implementer(IBlockFieldDeserializationTransformer)
class FormBlockDeserializer(FormBlockDeserializerBase):
    """Deserializer for content-types that implements IBlocks behavior"""


@adapter(IPloneSiteRoot, IBrowserRequest)
@implementer(IBlockFieldDeserializationTransformer)
class FormBlockDeserializerRoot(FormBlockDeserializerBase):
    """Deserializer for site root"""
