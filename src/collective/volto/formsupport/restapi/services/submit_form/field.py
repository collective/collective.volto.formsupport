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
    def value(self):
        if self._display_value_mapping:
            return self._display_value_mapping.get(self._value, self._value)
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    @property
    def label(self):
        return self._label if self._label else self.field_id

    @label.setter
    def label(self, label):
        self._label = label

    @property
    def field_id(self):
        if self._custom_field_id:
            return self._custom_field_id
        return self._field_id if self._field_id else self._label

    @field_id.setter
    def field_id(self, field_id):
        self._field_id = field_id

    @property
    def send_in_email(self):
        return True


class YesNoField(Field):
    @property
    def value(self):
        if self._display_value_mapping:
            if self._value is True:
                return self._display_value_mapping.get("yes")
            elif self._value is False:
                return self._display_value_mapping.get("no")
        return self._value

    @property
    def send_in_email(self):
        return True


class AttachmentField(Field):
    @property
    def send_in_email(self):
        return False


def construct_field(field_data):
    if field_data.get("widget") == "single_choice":
        return YesNoField(field_data)
    elif field_data.get("field_type") == "attachment":
        return AttachmentField(field_data)

    return Field(field_data)


def construct_fields(fields):
    return [construct_field(field) for field in fields]
