from extensions import db
from datetime import datetime
import uuid


class BlacklistEntry(db.Model):
    __tablename__ = "blacklist_entries"

    id            = db.Column(db.String(36),  primary_key=True, default=lambda: str(uuid.uuid4()))
    email         = db.Column(db.String(255), nullable=False, unique=True, index=True)
    app_uuid      = db.Column(db.String(36),  nullable=False)
    blocked_reason= db.Column(db.String(255), nullable=True)
    request_ip    = db.Column(db.String(45),  nullable=False)   # supports IPv6
    created_at    = db.Column(db.DateTime,    default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<BlacklistEntry email={self.email}>"
