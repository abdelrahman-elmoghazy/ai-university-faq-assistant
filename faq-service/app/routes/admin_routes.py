"""
Admin Routes — Team Member 5
Admin-only dashboard statistics and management endpoints.
"""
import logging
from flask import Blueprint, request, jsonify
from app.models.faq_models import db, Document, Question, Answer, AuditLog
from app.middleware.auth_middleware import token_required

logger = logging.getLogger(__name__)

admin_bp = Blueprint("faq_admin", __name__)


def admin_required(f):
    """Decorator: require admin role in JWT."""
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        roles = getattr(request, "roles", [])
        if "admin" not in roles:
            return jsonify({"error": "Forbidden", "message": "Admin role required."}), 403
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/stats", methods=["GET"])
@token_required
@admin_required
def get_dashboard_stats():
    """Return aggregated dashboard statistics for admin panel."""
    try:
        # Total users — count distinct user IDs from questions
        total_users_query = db.session.execute(
            db.text("SELECT COUNT(*) FROM users")
        ).scalar() or 0

        # Total uploaded files
        total_files = Document.query.count()

        # Total AI queries
        total_queries = Question.query.count()

        # Failed logins — from login_attempts table
        failed_logins = 0
        try:
            failed_logins = db.session.execute(
                db.text("SELECT COUNT(*) FROM login_attempts WHERE success = false")
            ).scalar() or 0
        except Exception:
            pass

        # Unauthorized attempts — from audit_logs
        unauthorized_attempts = 0
        try:
            unauthorized_attempts = db.session.execute(
                db.text("SELECT COUNT(*) FROM audit_logs WHERE status = 'failed'")
            ).scalar() or 0
        except Exception:
            pass

        # Processed / failed jobs from FAQ audit logs
        processed_jobs = AuditLog.query.filter_by(status="success").count()
        failed_jobs = AuditLog.query.filter_by(status="failed").count()

        return jsonify({
            "stats": {
                "total_users": total_users_query,
                "total_files": total_files,
                "total_queries": total_queries,
                "failed_logins": failed_logins,
                "unauthorized_attempts": unauthorized_attempts,
                "processed_jobs": processed_jobs,
                "failed_jobs": failed_jobs,
            }
        }), 200

    except Exception as e:
        logger.error(f"Dashboard stats error: {e}")
        return jsonify({"error": "Internal Server Error", "message": "Could not retrieve stats."}), 500


@admin_bp.route("/files", methods=["GET"])
@token_required
@admin_required
def get_all_files():
    """Get all uploaded files (admin only)."""
    try:
        from app.services.file_service import FileService
        files = FileService.get_all_files()
        return jsonify({"files": files}), 200
    except Exception as e:
        logger.error(f"Admin files error: {e}")
        return jsonify({"error": "Internal Server Error", "message": "Could not retrieve files."}), 500


@admin_bp.route("/audit-logs", methods=["GET"])
@token_required
@admin_required
def get_audit_logs():
    """Get recent audit logs (admin only)."""
    try:
        limit = request.args.get("limit", 50, type=int)
        logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(limit).all()
        return jsonify({
            "logs": [
                {
                    "id": log.id,
                    "user_id": log.user_id,
                    "action": log.action,
                    "status": log.status,
                    "ip_address": log.ip_address,
                    "details": log.details,
                    "created_at": log.created_at.isoformat()
                }
                for log in logs
            ]
        }), 200
    except Exception as e:
        logger.error(f"Audit logs error: {e}")
        return jsonify({"error": "Internal Server Error", "message": "Could not retrieve logs."}), 500


@admin_bp.route("/recent-queries", methods=["GET"])
@token_required
@admin_required
def get_recent_queries():
    """Get recent AI questions (admin only)."""
    try:
        limit = request.args.get("limit", 20, type=int)
        questions = Question.query.order_by(Question.created_at.desc()).limit(limit).all()
        return jsonify({
            "queries": [q.to_dict() for q in questions]
        }), 200
    except Exception as e:
        logger.error(f"Recent queries error: {e}")
        return jsonify({"error": "Internal Server Error", "message": "Could not retrieve queries."}), 500
