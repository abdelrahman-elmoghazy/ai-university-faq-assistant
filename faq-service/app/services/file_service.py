"""
File Service — Team Member 5
Handles secure file upload, validation, encryption, and storage.
"""
import os
import uuid
import logging
from datetime import datetime
from werkzeug.utils import secure_filename

from app.models.faq_models import db, Document
from app.services.encryption_service import (
    calculate_sha256, encrypt_file_data, decrypt_file_data
)

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/secure_uploads")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE_MB", "10")) * 1024 * 1024  # default 10 MB

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}
ALLOWED_MIMETYPES = {
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
BLOCKED_EXTENSIONS = {".exe", ".php", ".js", ".bat", ".sh", ".cmd", ".ps1", ".vbs"}


class FileService:
    """Secure file upload, storage, and retrieval."""

    @staticmethod
    def validate_file(file) -> tuple:
        """
        Validate uploaded file. Returns (is_valid, error_message).
        Checks: presence, size, extension, MIME type, blocked extensions.
        """
        if not file or file.filename == "":
            return False, "No file provided or filename is empty."

        # 1. Check filename and extension BEFORE reading content
        original_filename = secure_filename(file.filename)
        if not original_filename:
            return False, "Invalid filename."

        _, ext = os.path.splitext(original_filename)
        ext = ext.lower()

        # Security check: Block dangerous types first
        if ext in BLOCKED_EXTENSIONS:
            return False, "File type not allowed"

        if ext not in ALLOWED_EXTENSIONS:
            return False, f"File extension '{ext}' is not supported. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"

        # 2. Read file data for size and content checks
        file_data = file.read()
        file.seek(0)  # Reset for later use

        if len(file_data) == 0:
            return False, "Uploaded file is empty."

        if len(file_data) > MAX_FILE_SIZE:
            return False, f"File exceeds maximum size of {MAX_FILE_SIZE // (1024*1024)} MB."

        # 3. MIME type check (as a secondary layer)
        mime_type = file.content_type or ""
        if mime_type not in ALLOWED_MIMETYPES:
            return False, f"MIME type '{mime_type}' is not allowed."

        return True, None

    @staticmethod
    def upload_file(file, user_id: int) -> dict:
        """
        Process and store an uploaded file securely.
        Flow: validate → read → SHA-256 → encrypt → store → save metadata.
        """
        # Ensure upload directory exists
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        original_filename = secure_filename(file.filename)
        _, ext = os.path.splitext(original_filename)
        mime_type = file.content_type or "application/octet-stream"

        # Read raw file data
        raw_data = file.read()
        size_bytes = len(raw_data)

        # Defense-in-depth size check
        if size_bytes > MAX_FILE_SIZE:
            logger.warning(f"File rejected in service for user {user_id}: too large ({size_bytes} bytes)")
            raise ValueError(f"File exceeds maximum size of {MAX_FILE_SIZE // (1024*1024)} MB.")

        # Calculate SHA-256 BEFORE encryption
        sha256_hash = calculate_sha256(raw_data)

        # Encrypt file data
        encrypted_data = encrypt_file_data(raw_data)

        # Generate random stored filename
        stored_filename = f"{uuid.uuid4().hex}{ext}.enc"
        encrypted_path = os.path.join(UPLOAD_DIR, stored_filename)

        # Write encrypted file to disk
        with open(encrypted_path, "wb") as f:
            f.write(encrypted_data)

        # Save metadata to database
        doc = Document(
            title=original_filename,
            file_name=original_filename,
            stored_filename=stored_filename,
            file_path=encrypted_path,
            mime_type=mime_type,
            size_bytes=size_bytes,
            sha256_hash=sha256_hash,
            encrypted_path=encrypted_path,
            upload_status="completed",
            uploaded_by=user_id
        )
        db.session.add(doc)
        db.session.commit()

        # Trigger background processing (RAG Pipeline)
        from app.services.event_publisher import publish_document_event
        publish_document_event("document.uploaded", {
            "document_id": doc.id,
            "user_id": user_id,
            "filename": original_filename
        })

        logger.info(f"File uploaded: {original_filename} by user {user_id} → {stored_filename}")

        return {
            "id": doc.id,
            "original_filename": original_filename,
            "stored_filename": stored_filename,
            "mime_type": mime_type,
            "size_bytes": size_bytes,
            "sha256_hash": sha256_hash,
            "encrypted": True,
            "upload_status": "completed",
            "created_at": doc.created_at.isoformat()
        }

    @staticmethod
    def get_user_files(user_id: int) -> list:
        """Get all files uploaded by a specific user."""
        docs = Document.query.filter_by(uploaded_by=user_id)\
            .order_by(Document.created_at.desc()).all()
        return [FileService._doc_to_dict(d) for d in docs]

    @staticmethod
    def get_all_files() -> list:
        """Get all files (admin only)."""
        docs = Document.query.order_by(Document.created_at.desc()).all()
        return [FileService._doc_to_dict(d) for d in docs]

    @staticmethod
    def get_file_by_id(file_id: int, user_id: int, is_admin: bool = False) -> dict:
        """Get file metadata. Enforces ownership unless admin."""
        doc = Document.query.get(file_id)
        if not doc:
            return None

        if not is_admin and doc.uploaded_by != user_id:
            raise PermissionError("You do not have access to this file.")

        return FileService._doc_to_dict(doc)

    @staticmethod
    def verify_file_integrity(file_id: int, user_id: int, is_admin: bool = False) -> dict:
        """
        Verify SHA-256 integrity of a stored file.
        Decrypts in memory, recomputes hash, compares with stored hash.
        """
        from app.services.encryption_service import verify_integrity

        doc = Document.query.get(file_id)
        if not doc:
            return {"error": "File not found"}

        if not is_admin and doc.uploaded_by != user_id:
            raise PermissionError("You do not have access to this file.")

        if not doc.encrypted_path or not os.path.exists(doc.encrypted_path):
            return {"error": "Encrypted file not found on disk"}

        with open(doc.encrypted_path, "rb") as f:
            ciphertext = f.read()

        result = verify_integrity(doc.sha256_hash, ciphertext)
        result["file_id"] = doc.id
        result["original_filename"] = doc.file_name
        return result

    @staticmethod
    def _doc_to_dict(doc: Document) -> dict:
        """Convert Document model to safe dict for API response."""
        return {
            "id": doc.id,
            "original_filename": doc.file_name,
            "mime_type": doc.mime_type,
            "size_bytes": getattr(doc, "size_bytes", None),
            "sha256_hash": getattr(doc, "sha256_hash", None),
            "encrypted": True,
            "upload_status": getattr(doc, "upload_status", "completed"),
            "uploaded_by": doc.uploaded_by,
            "created_at": doc.created_at.isoformat()
        }
