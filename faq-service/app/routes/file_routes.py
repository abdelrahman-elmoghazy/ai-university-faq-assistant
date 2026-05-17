"""
File Routes — Team Member 5
Secure file upload, listing, and integrity verification endpoints.
"""
import logging
from flask import Blueprint, request, jsonify
from werkzeug.exceptions import RequestEntityTooLarge
from app.middleware.auth_middleware import token_required, get_client_ip
from app.services.file_service import FileService

logger = logging.getLogger(__name__)

file_bp = Blueprint("files", __name__)


@file_bp.route("/upload", methods=["POST"])
@token_required
def upload_file():
    """Upload a document securely."""
    try:
        if "file" not in request.files:
            return jsonify({"error": "Bad Request", "message": "No file part in request."}), 400

        file = request.files["file"]

        # Validate
        is_valid, error_msg = FileService.validate_file(file)
        if not is_valid:
            logger.warning(f"File rejected for user {request.user_id}: {error_msg}")
            return jsonify({"error": "Validation Error", "message": error_msg}), 400

        # Check visibility
        visibility = request.form.get("visibility", "private")
        if visibility == "public":
            is_admin = "admin" in getattr(request, "roles", [])
            if not is_admin:
                return jsonify({"error": "Forbidden", "message": "Only admins can upload public documents."}), 403
        else:
            visibility = "private"

        # Upload
        result = FileService.upload_file(file, request.user_id, visibility=visibility)

        logger.info(f"File uploaded by user {request.user_id}: {result['original_filename']}")
        return jsonify({"message": "File uploaded successfully", "file": result}), 201

    except RequestEntityTooLarge:
        logger.warning(f"File rejected for user {request.user_id}: file too large")
        return jsonify({
            "error": "File too large",
            "message": "Maximum allowed file size is 10 MB"
        }), 413
    except ValueError as ve:
        logger.warning(f"File validation error for user {request.user_id}: {ve}")
        return jsonify({"error": "Validation Error", "message": str(ve)}), 400
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred during upload."}), 500


@file_bp.route("/my-files", methods=["GET"])
@token_required
def get_my_files():
    """Get files uploaded by the current user."""
    try:
        files = FileService.get_user_files(request.user_id)
        return jsonify({"files": files}), 200
    except Exception as e:
        logger.error(f"Get files error: {e}")
        return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred."}), 500


@file_bp.route("/<int:file_id>", methods=["GET"])
@token_required
def get_file(file_id):
    """Get file metadata by ID (ownership enforced)."""
    try:
        is_admin = "admin" in getattr(request, "roles", [])
        result = FileService.get_file_by_id(file_id, request.user_id, is_admin=is_admin)
        if not result:
            return jsonify({"error": "Not Found", "message": "File not found."}), 404
        return jsonify({"file": result}), 200
    except PermissionError:
        return jsonify({"error": "Forbidden", "message": "You do not have access to this file."}), 403
    except Exception as e:
        logger.error(f"Get file error: {e}")
        return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred."}), 500


@file_bp.route("/<int:file_id>/verify", methods=["GET"])
@token_required
def verify_file(file_id):
    """Verify SHA-256 integrity of a stored file."""
    try:
        is_admin = "admin" in getattr(request, "roles", [])
        result = FileService.verify_file_integrity(file_id, request.user_id, is_admin=is_admin)
        if "error" in result:
            return jsonify(result), 404
        return jsonify(result), 200
    except PermissionError:
        return jsonify({"error": "Forbidden", "message": "You do not have access to this file."}), 403
    except Exception as e:
        logger.error(f"Verify file error: {e}")
        return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred."}), 500
