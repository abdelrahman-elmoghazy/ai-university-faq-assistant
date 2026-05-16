# Team Member 5 — Frontend, AI & File Security

## 📌 Role Overview

**Team Member 5** is responsible for building the user-facing React frontend, integrating AI-powered FAQ responses, implementing secure file upload with encryption, SHA-256 integrity verification, and the admin dashboard.

---

## 🖥️ Frontend Pages

| Page | Route | Access | Description |
|------|-------|--------|-------------|
| Login | `/login` | Public | Email + password authentication |
| Register | `/register` | Public | New user registration |
| Dashboard | `/dashboard` | Protected | User overview with stats |
| AI Chat | `/chat` | Protected | Ask university FAQ questions |
| File Upload | `/upload` | Protected | Secure document upload |
| Admin Dashboard | `/admin` | Admin Only | System stats and monitoring |
| Forbidden | `/forbidden` | Public | 403 error page |
| Not Found | `*` | Public | 404 error page |

### Tech Stack
- **React 18** + **Vite**
- **Tailwind CSS v4** with custom design system
- **React Router v6** with protected/admin route guards
- **Axios** with JWT interceptor
- Dark theme with glassmorphism effects

---

## 🤖 AI Integration Flow

```
User types question → Frontend sends POST /api/faq/ask
→ FAQ Service validates input (max 1000 chars)
→ FAQService._generate_ai_answer() called
→ AIService.generate_answer() invoked
→ Provider chain: OpenRouter → Ollama → Mock fallback
→ Answer saved to database
→ Response returned to frontend
→ Chat bubble displayed with answer
```

### Supported Providers

| Provider | Config | Description |
|----------|--------|-------------|
| **OpenRouter** | `AI_PROVIDER=openrouter` | Cloud API (GPT-3.5/4, Claude, etc.) |
| **Ollama** | `AI_PROVIDER=ollama` | Local model (Llama3, Mistral) |
| **Mock** | `AI_PROVIDER=mock` | Keyword-based demo responses |

### Setup
```bash
# OpenRouter
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-xxxxx

# Ollama (install from ollama.ai, run: ollama pull llama3)
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

---

## 📁 Secure File Upload Flow

```
User selects file → Frontend sends multipart POST /api/files/upload
→ FileService.validate_file():
  - Check file exists and is not empty
  - Check size ≤ 10 MB
  - Check extension is .pdf, .txt, or .docx
  - Block .exe, .php, .js, .bat, .sh
  - Validate MIME type matches
→ Read raw bytes
→ Calculate SHA-256 hash (BEFORE encryption)
→ Encrypt with Fernet (AES-128-CBC via cryptography library)
→ Generate random UUID filename
→ Store encrypted file in /app/secure_uploads/ (outside public folder)
→ Save metadata to documents table
→ Return file info + hash + encrypted status
```

---

## 🔐 Encryption Flow

```
Raw File Bytes → calculate_sha256(raw) → encrypt_file_data(raw) → Write .enc file
                      ↓                         ↓
                 Store hash             Store encrypted path
                 in database            in database
```

- **Algorithm**: Fernet (AES-128-CBC + HMAC-SHA256)
- **Key**: Environment variable `FILE_ENCRYPTION_KEY`
- **Generate key**: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- **Storage**: Only encrypted files are stored on disk
- **Access**: Decryption only for authorized users via API

---

## ✅ SHA-256 Integrity Verification Flow

```
User clicks "Verify Integrity" → GET /api/files/:id/verify
→ Read encrypted file from disk
→ Decrypt in memory (never stored decrypted)
→ Calculate SHA-256 of decrypted content
→ Compare with stored hash in database
→ Return: "valid" or "modified_or_corrupted"
```

---

## 🛡️ Admin Dashboard

Displays:
- Total users, files, AI queries
- Failed logins, unauthorized attempts
- Processed/failed background jobs
- Recent audit logs with timestamps
- Recent AI questions across all users

**Security**: Admin route requires `admin` role in JWT. Non-admin users see 403 Forbidden.

---

## 📡 API Endpoints Used

### Auth Service (Port 5000)
| Method | Endpoint | Auth |
|--------|----------|------|
| POST | `/api/auth/register` | Public |
| POST | `/api/auth/login` | Public |
| POST | `/api/auth/logout` | JWT |
| GET | `/api/auth/me` | JWT |

### FAQ Service (Port 5001) — Team Member 5 additions
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/faq/ask` | JWT | Ask AI question |
| GET | `/api/faq/history` | JWT | User's Q&A history |
| POST | `/api/files/upload` | JWT | Upload document |
| GET | `/api/files/my-files` | JWT | User's files |
| GET | `/api/files/:id` | JWT | File metadata |
| GET | `/api/files/:id/verify` | JWT | SHA-256 verification |
| GET | `/api/admin/stats` | Admin | Dashboard stats |
| GET | `/api/admin/files` | Admin | All files |
| GET | `/api/admin/audit-logs` | Admin | Audit logs |
| GET | `/api/admin/recent-queries` | Admin | Recent AI queries |

---

## ⚙️ Environment Variables

```env
# AI Configuration
AI_PROVIDER=mock              # openrouter | ollama | mock
OPENROUTER_API_KEY=           # Required if using openrouter
OPENROUTER_MODEL=openai/gpt-3.5-turbo
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# File Encryption
FILE_ENCRYPTION_KEY=          # Generate with Fernet.generate_key()
UPLOAD_DIR=/app/secure_uploads
MAX_FILE_SIZE_MB=10

# Frontend
VITE_API_BASE_URL=http://localhost:5000
```

---

## 🧪 Testing Checklist

### Frontend Tests
- [x] Register page renders and submits
- [x] Login page authenticates and redirects
- [x] Protected routes reject unauthenticated users
- [x] Admin routes reject normal users → Forbidden
- [x] Chat sends question and displays AI answer
- [x] Upload accepts valid file (PDF/TXT/DOCX)
- [x] Upload rejects invalid files

### Security Tests
- [x] .exe, .php, .js, .bat, .sh rejected
- [x] Wrong MIME type rejected
- [x] Oversized file rejected
- [x] Empty file rejected
- [x] Safe filename generated (UUID)
- [x] File stored encrypted on disk
- [x] File NOT in public folder

### Encryption Tests
- [x] Encrypted file exists on disk
- [x] Raw content not readable from stored file
- [x] Authorized user can access via API
- [x] Unauthorized user cannot access other's files

### Integrity Tests
- [x] Original file passes SHA-256 verification
- [x] Hash returned correctly in API response
- [x] Verification result displayed in frontend

### AI Tests
- [x] Authenticated user can ask question
- [x] Unauthenticated user gets 401
- [x] Very long question (>1000 chars) rejected
- [x] AI failure returns safe error message
- [x] AI query logged in audit

### Admin Tests
- [x] Admin sees dashboard stats
- [x] Normal user cannot access admin endpoints
- [x] Unauthorized attempts logged

---

## 🎬 Demo Steps

1. **Start services**: `docker-compose up --build`
2. **Open frontend**: `http://localhost:3000`
3. **Register** a new user account
4. **Login** with credentials
5. **Ask AI**: Go to Chat → type "What are admission requirements?"
6. **Upload file**: Go to Upload → upload a PDF file
7. **Verify integrity**: Click "Verify Integrity" button on uploaded file
8. **Admin panel**: Login as admin → view stats, logs, recent queries
9. **Security demo**: Try uploading .exe → shows rejection
10. **Access control**: Login as normal user → try `/admin` → shows 403

---

## 📸 Screenshots (Placeholders)

> _Replace with actual screenshots during presentation_

1. Login Page
2. Dashboard with stats
3. AI Chat conversation
4. File upload with encryption status
5. SHA-256 integrity verification result
6. Admin Dashboard with system stats
7. Forbidden page for unauthorized access

---

## 🔒 Security Requirements Covered

| Requirement | Status |
|-------------|--------|
| JWT Authentication | ✅ |
| RBAC (Admin/User roles) | ✅ |
| Protected routes | ✅ |
| File type validation (ext + MIME) | ✅ |
| Dangerous extension blocking | ✅ |
| File size limits | ✅ |
| Secure filename generation | ✅ |
| File stored outside public dir | ✅ |
| Fernet encryption at rest | ✅ |
| SHA-256 integrity verification | ✅ |
| User-scoped file access | ✅ |
| API keys server-side only | ✅ |
| Safe error messages | ✅ |
| Audit logging | ✅ |
| Input validation | ✅ |
