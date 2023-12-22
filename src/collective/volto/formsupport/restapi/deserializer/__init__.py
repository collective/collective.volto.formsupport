from plone.base.interfaces import IPloneSiteRoot
from plone.restapi.behaviors import IBlocks
from plone.restapi.interfaces import IBlockFieldSerializationTransformer
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


@implementer(IBlockFieldSerializationTransformer)
@adapter(IBlocks, IBrowserRequest)
class FormBlockSerializerBase:
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
        for field in data.get("subblocks", []):
            if len(field.get("validations", [])) > 0:
                self._expand_validation_field(field)

        return data

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
                field[validation_id] = settings

        # if api.user.has_permission("Modify portal content", obj=self.context):
        #     return value


@implementer(IBlockFieldSerializationTransformer)
@adapter(IBlocks, IBrowserRequest)
class FormBlockSerializer(FormBlockSerializerBase):
    """Serializer for content-types with IBlocks behavior"""


@implementer(IBlockFieldSerializationTransformer)
@adapter(IPloneSiteRoot, IBrowserRequest)
class FormBlockSerializerRoot(FormBlockSerializerBase):
    """Serializer for site root"""
