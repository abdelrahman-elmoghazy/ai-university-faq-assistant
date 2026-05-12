# AI University FAQ Assistant – System Documentation

## 📌 Overview

The AI University FAQ Assistant is a **secure, distributed microservices-based system** designed to handle university-related queries using AI-powered responses, authentication, and scalable backend services.

The system focuses on **security, modularity, and production-level architecture**, integrating multiple services including authentication, AI processing, FAQ management, background workers, and observability tools.

---

## 🧱 System Architecture

The system is built using a **microservices architecture**:

* Authentication Service (Auth & Security)
* API Gateway (Nginx Reverse Proxy)
* FAQ Service (Core Business Logic)
* AI Service (LLM Integration)
* Worker Service (Background Jobs)
* Logging & Monitoring Service
* Frontend (React Application)
* RabbitMQ (Message Broker)
* PostgreSQL (Database)

---

## 🔐 Authentication & Security System

### Features

* User registration and login
* JWT-based authentication (Access & Refresh tokens)
* OAuth2 login (Google, GitHub)
* Role-Based Access Control (RBAC)
* Password hashing using bcrypt/Argon2
* Internal service authentication (API keys)
* Audit logging for security events

### Security Rules

* No hardcoded secrets (all stored in `.env`)
* JWT secret validation enforced in production
* Protection against unauthorized access
* Users cannot access other users’ data
* Admin privilege protection

---

## 🌐 API Gateway Layer

The API Gateway acts as the **single entry point** for all requests.

### Responsibilities

* Reverse proxy routing (Nginx)
* HTTPS / SSL enforcement
* HTTP → HTTPS redirect
* Rate limiting
* Request size limiting
* Security headers enforcement
* Service isolation (no direct public access to internal services)

---

## 📚 FAQ Service (Core Backend)

### Features

* CRUD operations for FAQs
* Question & answer handling
* Conversation history
* PostgreSQL integration
* Input validation and sanitization
* Ownership checks for data access control

### Database Tables

* users
* roles
* permissions
* user_roles
* questions
* answers
* documents
* chunks
* audit_logs

---

## 🤖 AI Service

### Features

* AI-powered answer generation
* Integration with LLM providers (OpenRouter / Ollama)
* Context-aware responses using FAQ data
* Prompt engineering pipeline
* Vector database support (pgvector / Qdrant)

---

## ⚙️ Worker & Queue System

### Features

* RabbitMQ-based message queue
* Background job processing
* Document chunking
* Embedding generation
* Async processing pipeline

### Worker Tasks

* AI preprocessing jobs
* Document processing
* Logging events

---

## 📊 Logging & Monitoring System

### Features

* Centralized logging service
* Audit trail tracking
* Monitoring dashboard

### Logged Events

* Login attempts (success/failure)
* Logout events
* File uploads/downloads
* AI queries
* Unauthorized access attempts
* Background job status

---

## 🖥️ Frontend Application

### Features

* User authentication UI
* Dashboard
* Chat interface (AI assistant)
* Admin panel
* API integration layer

---

## 📁 File Security System

### Security Features

* File type validation (MIME + extension)
* Blocked extensions:

  * .exe
  * .php
  * .js
  * .bat
  * .sh
* File size limits
* Secure storage outside public directory
* File encryption (AES / Fernet)
* SHA-256 integrity verification

---

## 🗄️ Database Design (PostgreSQL)

### Core Tables

* users → user accounts
* roles → system roles
* permissions → access rules
* user_roles → role mapping
* questions → user queries
* answers → AI responses
* documents → uploaded files
* chunks → processed text segments
* audit_logs → system activity tracking

---

## 🔄 Authentication Flow

1. User registers or logs in
2. Credentials validated by Auth Service
3. JWT tokens generated (access + refresh)
4. Client includes token in requests
5. API Gateway validates token
6. Services enforce RBAC rules

---

## 🧪 Testing Strategy

### Authentication Testing

* Invalid login attempts
* Expired token validation
* Unauthorized access checks

### File Security Testing

* Valid file uploads
* Invalid file rejection
* Oversized file handling

### System Testing

* Rate limiting validation
* Internal service authentication
* Queue processing reliability

---

## 🐳 Deployment

### Docker Setup

```bash
docker-compose up --build
```

### Services Included

* auth-service
* faq-service
* ai-service
* worker-service
* api-gateway (nginx)
* postgres
* rabbitmq

---

## ⚙️ Environment Variables

All services use `.env` files for configuration:

```
DATABASE_URL=postgresql://user:pass@db:5432/app_db
JWT_SECRET_KEY=strong-secret-key
JWT_ALGORITHM=HS256
INTERNAL_API_KEY=secure-key
```

---

## 🚨 Security Best Practices

* Never commit `.env` files
* Enforce HTTPS in production
* Use strong JWT secrets
* Enable RBAC strictly
* Validate all inputs
* Restrict internal service access
* Monitor audit logs continuously

---

## 📈 Future Improvements

* Kubernetes deployment
* Redis caching layer
* Advanced rate limiting (user-based)
* AI response optimization
* Multi-language support
* Advanced threat detection system

---

## 📌 Summary

This system is designed to be a **secure, scalable, production-ready AI-powered university assistant platform** built with modern backend architecture principles, strong security layers, and modular microservices design.
