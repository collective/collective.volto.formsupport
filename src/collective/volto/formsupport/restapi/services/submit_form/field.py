from dataclasses import dataclass, InitVar
from typing import List, Optional, Any


@dataclass
class Field:
    field_id: str
    field_type: str
    id: str
    label: str
    show_when_when: str
    value: InitVar[Any]
    _value: Any = None
    input_values: Optional[List[dict]] = None
    internal_value: Optional[dict] = None
    required: Optional[str] = None
    widget: Optional[str] = None

    def __post_init__(self, value):
        self._value = value

    @property
    def value(self):
        if self.internal_value:
            return self.internal_value.get(self._value, self._value)
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    @property
    def send_in_email(self):
        return True


class YesNoField(Field):
    @property
    def value(self):
        if self.internal_value:
            if self._value is True:
                return self.internal_value.get("yes")
            elif self._value is False:
                return self.internal_value.get("no")
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
        return YesNoField(**field_data)
    elif field_data.get("field_type") == "attachment":
        return AttachmentField(**field_data)

    return Field(**field_data)


def construct_fields(fields):
    return [construct_field(field) for field in fields]
