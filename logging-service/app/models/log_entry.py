"""
LogEntry — persistent audit log stored in PostgreSQL.
"""
from datetime import datetime
from app import db


class LogEntry(db.Model):
    __tablename__ = "service_logs"

    id            = db.Column(db.Integer, primary_key=True)
    source        = db.Column(db.String(50), nullable=False, default="unknown")
    action        = db.Column(db.String(100), nullable=False)
    user_id       = db.Column(db.Integer, nullable=True)
    user_email    = db.Column(db.String(120), nullable=True)
    ip_address    = db.Column(db.String(45), nullable=True)
    status        = db.Column(db.String(20), nullable=True)
    details       = db.Column(db.JSON, nullable=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":         self.id,
            "source":     self.source,
            "action":     self.action,
            "user_id":    self.user_id,
            "user_email": self.user_email,
            "ip_address": self.ip_address,
            "status":     self.status,
            "details":    self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
