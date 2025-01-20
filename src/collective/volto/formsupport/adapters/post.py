from collective.volto.formsupport import _
from collective.volto.formsupport.interfaces import ICaptchaSupport
from collective.volto.formsupport.interfaces import IPostAdapter
from collective.volto.formsupport.restapi.services.submit_form.field import (
    construct_fields,
)
from collective.volto.formsupport.utils import get_blocks
from collective.volto.otp.utils import validate_email_token
from copy import deepcopy
from plone import api
from plone.restapi.deserializer import json_body
from zExceptions import BadRequest
from zope.component import adapter
from zope.component import getMultiAdapter
from zope.i18n import translate
from zope.interface import implementer
from zope.interface import Interface

import math
import os


@implementer(IPostAdapter)
@adapter(Interface, Interface)
class PostAdapter:
    block_id = None
    block = {}

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.form_data = self.extract_data_from_request()
        self.block_id = self.form_data.get("block_id", "")
        if self.block_id:
            self.block = self.get_block_data(block_id=self.block_id)

    def __call__(self):
        """
        Avoid XSS injections and other attacks.

        - cleanup HTML with plone transform
        - remove from data, fields not defined in form schema
        """

        self.validate_form()

        for field in self.filter_parameters():
            field.validate(request=self.request)

        return self.form_data

    def extract_data_from_request(self):
        form_data = json_body(self.request)

        fixed_fields = []
        transforms = api.portal.get_tool(name="portal_transforms")

        block = self.get_block_data(block_id=form_data.get("block_id", ""))
        block_fields = [x.get("field_id", "") for x in block.get("subblocks", [])]
        custom_block_fields = [
            block.get(field_id) for field_id in block_fields if block.get(field_id)
        ]

        for form_field in form_data.get("data", []):
            field_id = form_field.get("custom_field_id", form_field.get("field_id", ""))
            if field_id not in block_fields and field_id not in custom_block_fields:
                # unknown field, skip it
                continue
            new_field = deepcopy(form_field)
            value = new_field.get("value", "")
            if isinstance(value, str):
                stream = transforms.convertTo("text/plain", value, mimetype="text/html")
                new_field["value"] = stream.getData().strip()
            fixed_fields.append(new_field)

        form_data["data"] = fixed_fields

        return form_data

    def get_block_data(self, block_id):
        blocks = get_blocks(self.context)
        if not blocks:
            return {}
        for id, block in blocks.items():
            if id != block_id:
                continue
            block_type = block.get("@type", "")
            if block_type != "form":
                continue
            return block
        return {}

    def validate_form(self):
        """
        check all required fields and parameters
        """
        if not self.block_id:
            raise BadRequest(
                translate(
                    _("missing_blockid_label", default="Missing block_id"),
                    context=self.request,
                )
            )
        if not self.block:
            raise BadRequest(
                translate(
                    _(
                        "block_form_not_found_label",
                        default='Block with @type "form" and id "$block" not found in this context: $context',
                        mapping={
                            "block": self.block_id,
                            "context": self.context.absolute_url(),
                        },
                    ),
                    context=self.request,
                ),
            )

        if not self.block.get("store", False) and not self.block.get("send", []):
            raise BadRequest(
                translate(
                    _(
                        "missing_action",
                        default='You need to set at least one form action between "send" and "store".',  # noqa
                    ),
                    context=self.request,
                )
            )

        if not self.form_data.get("data", []):
            raise BadRequest(
                translate(
                    _(
                        "empty_form_data",
                        default="Empty form data.",
                    ),
                    context=self.request,
                )
            )

        self.validate_attachments()
        if self.block.get("captcha", False):
            getMultiAdapter(
                (self.context, self.request),
                ICaptchaSupport,
                name=self.block["captcha"],
            ).verify(self.form_data.get("captcha"))

        self.validate_bcc()

    def validate_bcc(self):
        """
        If otp validation is enabled, check if is valid
        """
        bcc_fields = []
        email_otp_verification = self.block.get("email_otp_verification", False)
        block_id = self.form_data.get("block_id", "")
        for field in self.block.get("subblocks", []):
            if field.get("use_as_bcc", False):
                field_id = field.get("field_id", "")
                if field_id not in bcc_fields:
                    bcc_fields.append(field_id)
        if not bcc_fields:
            return
        if not email_otp_verification:
            return
        for data in self.form_data.get("data", []):
            value = data.get("value", "")
            if not value:
                continue
            if data.get("field_id", "") not in bcc_fields:
                continue
            otp = data.get("otp", "")
            if not otp:
                raise BadRequest(
                    api.portal.translate(
                        _(
                            "otp_validation_missing_value",
                            default="Missing OTP value. Unable to submit the form.",
                        )
                    )
                )
            if not validate_email_token(block_id, value, otp):
                raise BadRequest(
                    api.portal.translate(
                        _(
                            "otp_validation_wrong_value",
                            default="${email}'s OTP is wrong",
                            mapping={"email": data["value"]},
                        )
                    )
                )

    def validate_attachments(self):
        attachments_limit = os.environ.get("FORM_ATTACHMENTS_LIMIT", "")
        if not attachments_limit:
            return
        attachments = self.form_data.get("attachments", {})
        attachments_len = 0
        for attachment in attachments.values():
            data = attachment.get("data", "")
            attachments_len += (len(data) * 3) / 4 - data.count("=", -2)
        if attachments_len > float(attachments_limit) * pow(1024, 2):
            size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
            i = int(math.floor(math.log(attachments_len, 1024)))
            p = math.pow(1024, i)
            s = round(attachments_len / p, 2)
            uploaded_str = f"{s} {size_name[i]}"
            raise BadRequest(
                translate(
                    _(
                        "attachments_too_big",
                        default="Attachments too big. You uploaded ${uploaded_str},"
                        " but limit is ${max} MB. Try to compress files.",
                        mapping={
                            "max": attachments_limit,
                            "uploaded_str": uploaded_str,
                        },
                    ),
                    context=self.request,
                )
            )

    def filter_parameters(self):
        """
        do not send attachments fields.
        """
        return [field for field in self.format_fields() if field.send_in_email]

    def format_fields(self):
        fields_data = []
        for submitted_field in self.form_data.get("data", []):
            # TODO: Review if fields submitted without a field_id should be included. Is breaking change if we remove it
            if submitted_field.get("field_id") is None:
                fields_data.append(submitted_field)
                continue
            for field in self.block.get("subblocks", []):
                if field.get("id", field.get("field_id")) == submitted_field.get(
                    "field_id"
                ):
                    fields_data.append(
                        {
                            **field,
                            **submitted_field,
                            "display_value_mapping": field.get("display_values"),
                            "custom_field_id": self.block.get(field["field_id"]),
                        }
                    )
        return construct_fields(fields_data)
