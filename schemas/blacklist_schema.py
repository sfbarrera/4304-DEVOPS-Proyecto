from extensions import ma
from models.blacklist import BlacklistEntry
from marshmallow import fields, validate, validates, ValidationError
import re


class BlacklistEntrySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = BlacklistEntry
        load_instance = True

    # ── Input fields (load_only) ─────────────────────────────────────────────
    email = fields.Email(
        required=True,
        load_only=False,
        metadata={"description": "Email address to add to the blacklist"}
    )
    app_uuid = fields.String(
        required=True,
        metadata={"description": "UUID of the client application"}
    )
    blocked_reason = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
        metadata={"description": "Optional reason for blocking (max 255 chars)"}
    )

    # ── Output-only fields ───────────────────────────────────────────────────
    id         = fields.String(dump_only=True)
    request_ip = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)

    @validates("app_uuid")
    def validate_app_uuid(self, value, **kwargs):
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            re.IGNORECASE,
        )
        if not uuid_pattern.match(value):
            raise ValidationError("app_uuid must be a valid UUID.")


blacklist_entry_schema  = BlacklistEntrySchema()
blacklist_entries_schema = BlacklistEntrySchema(many=True)
