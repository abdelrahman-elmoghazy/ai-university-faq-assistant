# FAQ Service API Documentation

## Overview
The FAQ Service handles the core business logic for user questions, generating AI responses, and maintaining conversation history. It integrates securely with the API Gateway and authenticates requests using JWT tokens from the Auth Service.

## Database Schema (PostgreSQL)

- **documents**: `id`, `title`, `file_name`, `file_path`, `mime_type`, `uploaded_by`, `created_at`
- **chunks**: `id`, `document_id` (FK), `chunk_text`, `chunk_index`, `embedding_status`, `created_at`
- **questions**: `id`, `user_id` (FK logical to Auth DB), `conversation_id`, `question_text`, `created_at`
- **answers**: `id`, `question_id` (FK), `answer_text`, `answer_source`, `created_at`
- **faq_audit_logs**: `id`, `user_id`, `action`, `status`, `ip_address`, `details`, `created_at`

## Authentication
All endpoints require a valid JWT token in the `Authorization: Bearer <token>` header. The JWT secret key must be identical to the one used by the Auth Service.

## API Endpoints

### 1. Ask a Question
- **URL**: `POST /api/faq/ask`
- **Headers**: `Authorization: Bearer <token>`
- **Request Body** (JSON):
  ```json
  {
    "question_text": "What is the university's attendance policy?",
    "conversation_id": "optional-uuid-here"
  }
  ```
- **Responses**:
  - `201 Created`: Successfully processed and returns the question and AI answer.
  - `400 Bad Request`: Validation failure (empty string, too long).
  - `401 Unauthorized`: Invalid or missing token.
  - `500 Internal Server Error`: Safe generic error response.

### 2. Get User Questions
- **URL**: `GET /api/faq/questions`
- **Headers**: `Authorization: Bearer <token>`
- **Responses**:
  - `200 OK`: Returns an array of the authenticated user's questions.

### 3. Get Question by ID
- **URL**: `GET /api/faq/questions/:id`
- **Headers**: `Authorization: Bearer <token>`
- **Responses**:
  - `200 OK`: Returns the requested question.
  - `403 Forbidden`: User attempts to access a question they do not own.
  - `404 Not Found`: Question does not exist.

### 4. Get Conversation History
- **URL**: `GET /api/faq/conversations`
- **Headers**: `Authorization: Bearer <token>`
- **Responses**:
  - `200 OK`: Returns a list of unique `conversation_id`s belonging to the user.

### 5. Get Question-Answer History
- **URL**: `GET /api/faq/history`
- **Headers**: `Authorization: Bearer <token>`
- **Responses**:
  - `200 OK`: Returns the complete history (questions + nested answers) for the authenticated user.
