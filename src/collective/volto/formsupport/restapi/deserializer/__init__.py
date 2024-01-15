from plone.base.interfaces import IPloneSiteRoot
from plone.restapi.behaviors import IBlocks
from plone.restapi.interfaces import IBlockFieldDeserializationTransformer

# from plone.restapi.interfaces import IBlockFieldSerializationTransformer
from zope.component import adapter
from zope.interface import implementer
from zope.publisher.interfaces.browser import IBrowserRequest

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

python_type_to_volto_type_mapping = {
    "int": "integer",
    "float": "number",
    "bool": "boolean",
}


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
        # Field is the full field definition
        for index, field in enumerate(data.get("subblocks", [])):
            if len(field.get("validations", [])) > 0:
                data["subblocks"][index] = self._update_validations(field)

        return data

    def _update_validations(self, field):
        validations = field.get("validations")
        new_settings = field.get("validationSettings")
        # The settings were collapsed on the frontend, we need to find the validation it was for
        for validation_id in validations:
            settings = (
                {
                    setting_name: val
                    for setting_name, val in new_settings.items()
                    if setting_name not in IGNORED_VALIDATION_DEFINITION_ARGUMENTS
                }
                if field.get(validation_id)
                else None
            )
            if settings:
                field[validation_id] = settings

                validation_to_update = [
                    validation
                    for validation in getValidations()
                    if validation[0] == validation_id
                ][0][1]
                for setting_id, setting_value in settings.items():
                    validation_to_update._settings[setting_id] = setting_value

        return field


@implementer(IBlockFieldDeserializationTransformer)
@adapter(IBlocks, IBrowserRequest)
class FormBlockDeserializer(FormBlockDeserializerBase):
    """Serializer for content-types with IBlocks behavior"""


@implementer(IBlockFieldDeserializationTransformer)
@adapter(IPloneSiteRoot, IBrowserRequest)
class FormBlockDeserializerRoot(FormBlockDeserializerBase):
    """Serializer for site root"""
