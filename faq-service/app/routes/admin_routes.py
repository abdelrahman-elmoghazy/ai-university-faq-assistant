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

@admin_bp.route("/users", methods=["GET"])
@token_required
@admin_required
def get_all_users():
    """Get all users (admin only). Read-only from FAQ service."""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        offset = (page - 1) * per_page

        # Execute raw SQL to fetch users
        total = db.session.execute(db.text("SELECT COUNT(*) FROM users")).scalar() or 0
        pages = (total + per_page - 1) // per_page

        users_result = db.session.execute(
            db.text("SELECT id, username, email, full_name, is_active, created_at, last_login FROM users ORDER BY created_at DESC LIMIT :limit OFFSET :offset"),
            {"limit": per_page, "offset": offset}
        ).fetchall()

        users = []
        for u in users_result:
            roles_result = db.session.execute(
                db.text("SELECT r.name FROM roles r JOIN user_roles ur ON r.id = ur.role_id WHERE ur.user_id = :user_id"),
                {"user_id": u.id}
            ).fetchall()
            
            users.append({
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "full_name": u.full_name,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "last_login": u.last_login.isoformat() if u.last_login else None,
                "roles": [{"name": r.name} for r in roles_result]
            })

        return jsonify({
            "users": users,
            "total": total,
            "pages": pages,
            "current_page": page
        }), 200
    except Exception as e:
        logger.error(f"Admin get users error: {e}")
        return jsonify({"error": "Internal Server Error", "message": "Could not retrieve users."}), 500

@admin_bp.route("/users/<int:user_id>/role", methods=["PATCH"])
@token_required
@admin_required
def update_user_role(user_id):
    """Update user role (admin only). Manage roles directly in FAQ service."""
    try:
        if user_id == request.user_id:
            return jsonify({"error": "Forbidden", "message": "Cannot modify own role"}), 403

        data = request.get_json()
        if not data or "role" not in data or "action" not in data:
            return jsonify({"error": "Bad Request", "message": "role and action are required"}), 400

        role_name = data.get("role")
        action = data.get("action")

        if action not in ["add", "remove"]:
            return jsonify({"error": "Bad Request", "message": "Action must be add or remove"}), 400

        # Find user
        user_exists = db.session.execute(db.text("SELECT id FROM users WHERE id = :user_id"), {"user_id": user_id}).scalar()
        if not user_exists:
            return jsonify({"error": "Not Found", "message": "User not found"}), 404

        # Find role
        role_id = db.session.execute(db.text("SELECT id FROM roles WHERE name = :role_name"), {"role_name": role_name}).scalar()
        if not role_id:
            return jsonify({"error": "Not Found", "message": f"Role '{role_name}' not found"}), 404

        # Check existing mapping
        exists = db.session.execute(
            db.text("SELECT 1 FROM user_roles WHERE user_id = :user_id AND role_id = :role_id"),
            {"user_id": user_id, "role_id": role_id}
        ).scalar()

        if action == "add" and not exists:
            db.session.execute(
                db.text("INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)"),
                {"user_id": user_id, "role_id": role_id}
            )
        elif action == "remove" and exists:
            db.session.execute(
                db.text("DELETE FROM user_roles WHERE user_id = :user_id AND role_id = :role_id"),
                {"user_id": user_id, "role_id": role_id}
            )

        db.session.commit()

        # Log action
        try:
            import json
            audit = AuditLog(
                user_id=request.user_id,
                action=f"{action}_role",
                status="success",
                details=json.dumps({"target_user_id": user_id, "role": role_name})
            )
            db.session.add(audit)
            db.session.commit()
        except Exception as audit_err:
            db.session.rollback()
            logger.warning(f"Failed to log role update action: {audit_err}")

        # Fetch updated roles
        roles_result = db.session.execute(
            db.text("SELECT r.name FROM roles r JOIN user_roles ur ON r.id = ur.role_id WHERE ur.user_id = :user_id"),
            {"user_id": user_id}
        ).fetchall()
        updated_roles = [r.name for r in roles_result]

        return jsonify({
            "message": "User role updated successfully",
            "user_id": user_id,
            "roles": updated_roles
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Admin update role error: {e}")
        return jsonify({"error": "Internal Server Error", "message": "Could not update user role."}), 500

@admin_bp.route("/files/<int:file_id>", methods=["DELETE"])
@token_required
@admin_required
def delete_file(file_id):
    """Delete a file (admin only)."""
    try:
        from app.services.file_service import FileService
        # Get filename before delete for logging
        file_meta = FileService.get_file_by_id(file_id, request.user_id, is_admin=True)
        if not file_meta:
            return jsonify({"error": "Not found", "message": "File not found"}), 404
            
        result = FileService.delete_file(file_id, request.user_id, is_admin=True)
        if not result:
            return jsonify({"error": "Not found", "message": "File not found"}), 404
            
        # Log action
        try:
            import json
            audit = AuditLog(
                user_id=request.user_id,
                action="delete_file_admin",
                status="success",
                details=json.dumps({"file_id": file_id, "filename": file_meta.get("original_filename")})
            )
            db.session.add(audit)
            db.session.commit()
        except Exception as audit_err:
            db.session.rollback()
            logger.warning(f"Failed to log admin file delete action: {audit_err}")
            
        return jsonify({"message": "File deleted successfully", "file_id": file_id}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Admin file delete error: {e}")
        return jsonify({"error": "Internal Server Error", "message": "Could not delete file."}), 500


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
