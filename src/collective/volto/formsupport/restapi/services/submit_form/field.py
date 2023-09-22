from dataclasses import dataclass
from typing import List, Optional, Any


@dataclass
class Field:
    field_id: str
    field_type: str
    id: str
    label: str
    required: str
    show_when_when: str
    submitted_value: Any
    input_values: Optional[List[dict]] = None
    internal_value: Optional[dict] = None
    widget: Optional[str] = None

    def get_display_value(self):
        if self.internal_value:
            return self.internal_value.get(self.submitted_value, self.submitted_value)
        return self.submitted_value

    @property
    def send_in_email(self):
        return True


class YesNoField(Field):
    def get_display_value(self):
        if self.internal_value:
            if self.submitted_value is True:
                return self.internal_value.get("yes")
            elif self.submitted_value is False:
                return self.internal_value.get("yes")
        return self.submitted_value

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
