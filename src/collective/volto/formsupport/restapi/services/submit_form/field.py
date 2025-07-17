from collective.volto.formsupport import _
from plone import api
from plone.schema.email import _isemail
from zExceptions import BadRequest
from zope.i18n import translate


class Field:
    def __init__(self, field_data):
        def _attribute(attribute_name):
            setattr(self, attribute_name, field_data.get(attribute_name))

        _attribute("field_type")
        _attribute("id")
        _attribute("show_when_when")
        _attribute("show_when_is")
        _attribute("show_when_to")
        _attribute("input_values")
        _attribute("required")
        _attribute("widget")
        _attribute("use_as_reply_to")
        _attribute("use_as_reply_bcc")
        self._display_value_mapping = field_data.get("display_value_mapping")
        self._value = field_data.get("value", "")
        self._custom_field_id = field_data.get("custom_field_id")
        self._label = field_data.get("label", "")
        self._field_id = field_data.get("field_id", "")

    @property
    def display_value(self):
        if self._display_value_mapping:
            return self._display_value_mapping.get(self._value, self._value)
        if isinstance(self._value, list):
            return  ", ".join(self._value)
        return self._value

    @property
    def internal_value(self):
        return self._value

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
        return


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
        super().validate(request=request)

        if not _isemail(self.internal_value):
            raise BadRequest(
                translate(
                    _(
                        "wrong_email",
                        default='Email not valid in "${field}" field.',
                        mapping={
                            "field": self.label,
                        },
                    ),
                    context=request,
                )
            )


class DateField(Field):
    def display_value(self):
        return api.portal.get_localized_time(self.internal_value)


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
