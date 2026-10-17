from datetime import datetime, timezone

from ..extensions import db


class BlacklistEntry(db.Model):
    __tablename__ = "blacklist"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(320), nullable=False, unique=True, index=True)
    app_uuid = db.Column(db.Uuid, nullable=False)
    blocked_reason = db.Column(db.String(255))
    ip_address = db.Column(db.String(45), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
