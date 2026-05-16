# FAQ Service

Handles user questions, AI-powered responses, file uploads, and conversation history.
Authenticates requests using JWT tokens from the Auth Service.

## Database Tables

- **documents**: id, title, file_name, file_path, mime_type, uploaded_by, created_at
- **chunks**: id, document_id (FK), chunk_text, chunk_index, embedding_status, created_at
- **questions**: id, user_id, conversation_id, question_text, created_at
- **answers**: id, question_id (FK), answer_text, answer_source, created_at
- **faq_audit_logs**: id, user_id, action, status, ip_address, details, created_at

## Endpoints

All endpoints require `Authorization: Bearer <token>` header.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/faq/ask` | Ask a question (AI generates answer) |
| GET | `/api/faq/questions` | List user's questions |
| GET | `/api/faq/questions/:id` | Get specific question (ownership enforced) |
| GET | `/api/faq/conversations` | List user's conversation IDs |
| GET | `/api/faq/history` | Full Q&A history for the user |
| POST | `/api/files/upload` | Upload a document (validated + encrypted) |
| GET | `/api/files/my-files` | List user's uploaded files |
| GET | `/api/files/:id/verify` | SHA-256 integrity check |
| GET | `/api/admin/stats` | System stats (admin only) |
| GET | `/api/admin/audit-logs` | Audit log entries (admin only) |
