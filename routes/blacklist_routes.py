from flask import Blueprint, request
from flask_restful import Api, Resource
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from extensions import db
from models.blacklist import BlacklistEntry
from schemas.blacklist_schema import blacklist_entry_schema

blacklist_bp = Blueprint("blacklist", __name__)
api = Api(blacklist_bp)

VERSION = "all-at-once-v1"


# ── Helper ────────────────────────────────────────────────────────────────────

def get_client_ip():
    """Return the real client IP, accounting for proxies/load-balancers."""
    if request.headers.get("X-Forwarded-For"):
        return request.headers["X-Forwarded-For"].split(",")[0].strip()
    return request.remote_addr or "unknown"


# ── Resources ─────────────────────────────────────────────────────────────────

class BlacklistResource(Resource):
    """POST /blacklists — add an email to the global blacklist."""

    @jwt_required()
    def post(self):
        json_data = request.get_json(silent=True)
        if not json_data:
            return {"msg": "No JSON body provided.", "version": VERSION}, 400

        # ── Validate & deserialise ────────────────────────────────────────────
        try:
            data = blacklist_entry_schema.load(json_data, session=db.session)
        except ValidationError as err:
            return {"msg": "Validation error.", "errors": err.messages, "version": VERSION}, 400

        # ── Duplicate check ───────────────────────────────────────────────────
        existing = BlacklistEntry.query.filter_by(email=data.email).first()
        if existing:
            return {
                "msg": f"The email '{data.email}' is already in the blacklist.",
                "id": existing.id,
                "version": VERSION,
            }, 409

        # ── Enrich with server-side fields ────────────────────────────────────
        data.request_ip = get_client_ip()

        # ── Persist ───────────────────────────────────────────────────────────
        db.session.add(data)
        db.session.commit()

        return {
            "msg": f"Email '{data.email}' was successfully added to the blacklist.",
            "id": data.id,
            "version": VERSION,
        }, 201


class BlacklistQueryResource(Resource):
    """GET /blacklists/<email> — check if an email is blacklisted."""

    @jwt_required()
    def get(self, email):
        entry = BlacklistEntry.query.filter_by(email=email).first()

        if entry:
            return {
                "blacklisted": True,
                "email": entry.email,
                "blocked_reason": entry.blocked_reason,
                "created_at": entry.created_at.isoformat(),
                "version": VERSION,
            }, 200
        else:
            return {
                "blacklisted": False,
                "email": email,
                "blocked_reason": None,
                "version": VERSION,
            }, 200


# ── Register routes ───────────────────────────────────────────────────────────
api.add_resource(BlacklistResource,      "/blacklists")
api.add_resource(BlacklistQueryResource, "/blacklists/<string:email>")
