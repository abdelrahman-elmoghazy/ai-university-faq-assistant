"""
Team Member 5 — Backend Test Suite
Tests for file upload security, encryption, integrity, AI, and admin endpoints.
Run with: pytest tests/test_team5_backend.py -v
"""
import os
import sys
import json
import hashlib
import pytest

# ── Add faq-service to path ──────────────────────────────────
FAQ_SERVICE_DIR = os.path.join(os.path.dirname(__file__), '..', 'faq-service')
sys.path.insert(0, FAQ_SERVICE_DIR)


# ════════════════════════════════════════════════════════════
#  1. ENCRYPTION SERVICE TESTS
# ════════════════════════════════════════════════════════════

class TestEncryptionService:
    """Tests for Fernet encryption and SHA-256 hashing."""

    def test_sha256_hash_correct(self):
        from app.services.encryption_service import calculate_sha256
        data = b"Hello, University!"
        expected = hashlib.sha256(data).hexdigest()
        assert calculate_sha256(data) == expected

    def test_sha256_different_data_different_hash(self):
        from app.services.encryption_service import calculate_sha256
        h1 = calculate_sha256(b"file_a_content")
        h2 = calculate_sha256(b"file_b_content")
        assert h1 != h2

    def test_encrypt_decrypt_roundtrip(self):
        """Encrypted data should decrypt back to original."""
        # Generate a test key
        from cryptography.fernet import Fernet
        key = Fernet.generate_key().decode()
        os.environ['FILE_ENCRYPTION_KEY'] = key
        # Reload module to pick up new key
        import importlib
        from app.services import encryption_service
        importlib.reload(encryption_service)

        plaintext = b"This is a confidential university document."
        ciphertext = encryption_service.encrypt_file_data(plaintext)
        assert ciphertext != plaintext  # Must be encrypted
        decrypted = encryption_service.decrypt_file_data(ciphertext)
        assert decrypted == plaintext

    def test_encrypted_file_not_readable(self):
        """Raw ciphertext should not contain the original content."""
        from cryptography.fernet import Fernet
        key = Fernet.generate_key().decode()
        os.environ['FILE_ENCRYPTION_KEY'] = key
        import importlib
        from app.services import encryption_service
        importlib.reload(encryption_service)

        plaintext = b"Sensitive student records"
        ciphertext = encryption_service.encrypt_file_data(plaintext)
        assert plaintext not in ciphertext

    def test_integrity_verification_valid(self):
        """Valid file should pass integrity check."""
        from cryptography.fernet import Fernet
        key = Fernet.generate_key().decode()
        os.environ['FILE_ENCRYPTION_KEY'] = key
        import importlib
        from app.services import encryption_service
        importlib.reload(encryption_service)

        plaintext = b"University FAQ Document"
        sha = encryption_service.calculate_sha256(plaintext)
        ciphertext = encryption_service.encrypt_file_data(plaintext)
        result = encryption_service.verify_integrity(sha, ciphertext)
        assert result['integrity_status'] == 'valid'

    def test_integrity_verification_corrupted(self):
        """Modified file should fail integrity check."""
        from cryptography.fernet import Fernet
        key = Fernet.generate_key().decode()
        os.environ['FILE_ENCRYPTION_KEY'] = key
        import importlib
        from app.services import encryption_service
        importlib.reload(encryption_service)

        original = b"Original content"
        wrong_hash = "0" * 64  # Fake hash
        ciphertext = encryption_service.encrypt_file_data(original)
        result = encryption_service.verify_integrity(wrong_hash, ciphertext)
        assert result['integrity_status'] == 'modified_or_corrupted'


# ════════════════════════════════════════════════════════════
#  2. FILE VALIDATION TESTS
# ════════════════════════════════════════════════════════════

class TestFileValidation:
    """Tests for file extension and MIME type validation."""

    def test_blocked_extensions(self):
        from app.services.file_service import BLOCKED_EXTENSIONS
        for ext in ['.exe', '.php', '.js', '.bat', '.sh']:
            assert ext in BLOCKED_EXTENSIONS, f"{ext} should be blocked"

    def test_allowed_extensions(self):
        from app.services.file_service import ALLOWED_EXTENSIONS
        for ext in ['.pdf', '.txt', '.docx']:
            assert ext in ALLOWED_EXTENSIONS, f"{ext} should be allowed"

    def test_allowed_mimetypes(self):
        from app.services.file_service import ALLOWED_MIMETYPES
        assert 'application/pdf' in ALLOWED_MIMETYPES
        assert 'text/plain' in ALLOWED_MIMETYPES


# ════════════════════════════════════════════════════════════
#  3. AI SERVICE TESTS
# ════════════════════════════════════════════════════════════

class TestAIService:
    """Tests for AI answer generation."""

    def test_mock_response_returns_string(self):
        os.environ['AI_PROVIDER'] = 'mock'
        from app.services.ai_service import AIService
        answer = AIService.generate_answer("What are admission requirements?")
        assert isinstance(answer, str)
        assert len(answer) > 0

    def test_mock_response_keyword_match(self):
        os.environ['AI_PROVIDER'] = 'mock'
        from app.services.ai_service import AIService
        answer = AIService.generate_answer("Tell me about tuition fees")
        assert 'tuition' in answer.lower() or 'fee' in answer.lower() or 'program' in answer.lower()

    def test_fallback_on_invalid_provider(self):
        os.environ['AI_PROVIDER'] = 'nonexistent_provider'
        from app.services.ai_service import AIService
        answer = AIService.generate_answer("Test question")
        assert isinstance(answer, str)
        assert len(answer) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
