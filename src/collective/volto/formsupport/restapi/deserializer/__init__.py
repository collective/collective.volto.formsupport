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
        validation_ids_on_field = field.get("validations")
        all_validation_settings = field.get("validationSettings")

        if not validation_ids_on_field:
            field["validationSettings"] = {}
            return field

        # The settings were collapsed to a single control on the frontend, we need to find the validation it was for and tidy things up before continuing
        all_setting_ids = all_validation_settings.keys()
        top_level_setting_ids = []
        for validation_id in validation_ids_on_field:
            id_to_check = f"{validation_id}-"
            for setting_id in all_setting_ids:
                if setting_id.startswith(id_to_check):
                    top_level_setting_ids.append(setting_id)
        for top_level_setting_id in top_level_setting_ids:
            validation_id, setting_id = top_level_setting_id.split("-")
            all_validation_settings[validation_id][
                setting_id
            ] = all_validation_settings[top_level_setting_id]

        # update the internal definitions for the field settings
        for validation_id in validation_ids_on_field:
            validation_to_update = [
                validation
                for validation in getValidations()
                if validation[0] == validation_id
            ][0][1]

            validation_settings = all_validation_settings.get(validation_id)

            if validation_settings:
                for setting_name, setting_value in all_validation_settings[
                    validation_id
                ].items():
                    if setting_name in IGNORED_VALIDATION_DEFINITION_ARGUMENTS:
                        continue
                    validation_to_update._settings[setting_name] = setting_value

            field["validationSettings"][validation_id] = {
                k: v
                for k, v in validation_to_update.settings.items()
                if k not in IGNORED_VALIDATION_DEFINITION_ARGUMENTS
            }

        # Remove any old settings
        keys_to_delete = []
        for key in all_validation_settings.keys():
            if key not in validation_ids_on_field:
                keys_to_delete.append(key)
        for key in keys_to_delete:
            del all_validation_settings[key]

        return field


@implementer(IBlockFieldDeserializationTransformer)
@adapter(IBlocks, IBrowserRequest)
class FormBlockDeserializer(FormBlockDeserializerBase):
    """Serializer for content-types with IBlocks behavior"""


@implementer(IBlockFieldDeserializationTransformer)
@adapter(IPloneSiteRoot, IBrowserRequest)
class FormBlockDeserializerRoot(FormBlockDeserializerBase):
    """Serializer for site root"""
