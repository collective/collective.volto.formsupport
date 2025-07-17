import re
from typing import Any

from collective.volto.formsupport import _
from collective.volto.formsupport.validation import getValidations
from plone import api
from plone.schema.email import _isemail
from zExceptions import BadRequest
from zope.i18n import translate

validation_message_matcher = re.compile("Validation failed\(([^\)]+)\): ")


def always():
    return True


def value_is(value, target_value):
    if isinstance(target_value, list):
        return value in target_value
    return value == target_value


def value_is_not(value, target_value):
    if isinstance(target_value, list):
        return value not in target_value
    return value != target_value


show_when_validators = {
    "": always,
    "always": always,
    "value_is": value_is,
    "value_is_not": value_is_not,
}


class Field:
    def __init__(self, field_data: dict[str, Any]):
        def _attribute(attribute_name: str):
            setattr(self, attribute_name, field_data.get(attribute_name))

        _attribute("field_type")
        _attribute("id")
        _attribute("show_when_when")
        _attribute("show_when_is")
        _attribute("show_when_to")
        _attribute("input_values")
        _attribute("widget")
        _attribute("use_as_reply_to")
        _attribute("use_as_reply_bcc")
        self.required = field_data.get("required")
        self.validations = field_data.get("validations", {})
        self._display_value_mapping = field_data.get("dislpay_value_mapping")
        self._value = field_data.get("value", "")
        self._custom_field_id = field_data.get("custom_field_id")
        self._label = field_data.get("label", "")
        self._field_id = field_data.get("field_id", "")

    @property
    def display_value(self):
        if self._display_value_mapping:
            return self._display_value_mapping.get(self._value, self._value)
        if isinstance(self._value, list):
            return ", ".join(self._value)
        return self._value

    @property
    def internal_value(self):
        return self._value

    def should_show(self, show_when_is, target_value):
        always_show_validator = show_when_validators["always"]
        if not show_when_is:
            return always_show_validator()
        show_when_validator = show_when_validators[show_when_is]
        if not show_when_validator:
            return always_show_validator
        return show_when_validator(value=self.value, target_value=target_value)

    @property
    def label(self):
        return self._label if self._label else self.field_id

    @property
    def field_id(self):
        if self._custom_field_id:
            return self._custom_field_id
        return self._field_id if self._field_id else self._label

    @property
    def send_in_email(self):
        return True

    def validate(self, request):
        # Making sure we've got a validation that actually exists.
        if not self._value and not self.required:
            return
        errors = {}

        if self.required and not self.internal_value:
            errors["required"] = "This field is required"

        available_validations = [
            validation
            for validationId, validation in getValidations()
            if validationId in self.validations.keys()
        ]
        for validation in available_validations:
            error = validation(self._value, **self.validations.get(validation._name))
            if error:
                match_result = validation_message_matcher.match(error)
                # We should be able to clean up messages that follow the
                #   `Validation failed({validation_id}): {message}` pattern.
                #   No guarantees we will encounter it though.
                if match_result:
                    error = validation_message_matcher.sub("", error)

                errors[validation._name] = error

        return (
            errors
        )  # Return None to match how errors normally return in z3c.form


class YesNoField(Field):
    @property
    def display_value(self):
        if not self._display_value_mapping:
            return self.internal_value
        if self.internal_value is True:
            return self._display_value_mapping.get("yes")
        elif self.internal_value is False:
            return self._display_value_mapping.get("no")


class AttachmentField(Field):
    @property
    def send_in_email(self):
        return False


class EmailField(Field):
    def validate(self, request):
        errors = super().validate(request=request)
        if not self.internal_value:
            return
        if not _isemail(self.internal_value or ""):
            errors["validation"] = translate(
                _(
                    "wrong_email",
                    default='Email not valid in "${field}" field.',
                    mapping={
                        "field": self.label,
                    },
                ),
                context=request,
            )
        return errors


class DateField(Field):
    def display_value(self):
        return api.portal.get_localized_time(self.internal_value or "")


def construct_field(field_data):
    if field_data.get("widget") == "single_choice":
        return YesNoField(field_data)
    elif field_data.get("field_type") == "attachment":
        return AttachmentField(field_data)
    elif field_data.get("field_type") in ["from", "email"]:
        return EmailField(field_data)
    elif field_data.get("field_type") == "date":
        return DateField(field_data)

    return Field(field_data)


def construct_fields(fields):
    return [construct_field(field) for field in fields]
