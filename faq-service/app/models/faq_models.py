from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=True)   # random name on disk
    file_path = db.Column(db.String(500), nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    size_bytes = db.Column(db.BigInteger, nullable=True)
    sha256_hash = db.Column(db.String(64), nullable=True)        # SHA-256 hex digest
    encrypted_path = db.Column(db.String(500), nullable=True)    # path to encrypted file
    upload_status = db.Column(db.String(50), default='pending')  # pending, completed, failed
    visibility = db.Column(db.String(20), default='private')     # private, public
    uploaded_by = db.Column(db.Integer, nullable=False, index=True) # user_id from auth_service
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    chunks = db.relationship('Chunk', backref='document', lazy=True, cascade='all, delete-orphan')

    def __init__(self, title: str, file_name: str, file_path: str, mime_type: str, uploaded_by: int, stored_filename: str = None, size_bytes: int = None, sha256_hash: str = None, encrypted_path: str = None, upload_status: str = 'pending', visibility: str = 'private', **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.file_name = file_name
        self.file_path = file_path
        self.mime_type = mime_type
        self.uploaded_by = uploaded_by
        self.stored_filename = stored_filename
        self.size_bytes = size_bytes
        self.sha256_hash = sha256_hash
        self.encrypted_path = encrypted_path
        self.upload_status = upload_status
        self.visibility = visibility

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'file_name': self.file_name,
            'mime_type': self.mime_type,
            'size_bytes': self.size_bytes,
            'sha256_hash': self.sha256_hash,
            'encrypted': bool(self.encrypted_path),
            'upload_status': self.upload_status,
            'visibility': self.visibility,
            'uploaded_by': self.uploaded_by,
            'created_at': self.created_at.isoformat()
        }

class Chunk(db.Model):
    __tablename__ = 'chunks'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    chunk_text = db.Column(db.Text, nullable=False)
    chunk_index = db.Column(db.Integer, nullable=False)
    embedding_status = db.Column(db.String(50), default='pending') # pending, completed, failed
    from pgvector.sqlalchemy import Vector
    embedding = db.Column(Vector(384))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, document_id: int, chunk_text: str, chunk_index: int, embedding_status: str = 'pending', embedding = None, **kwargs):
        super().__init__(**kwargs)
        self.document_id = document_id
        self.chunk_text = chunk_text
        self.chunk_index = chunk_index
        self.embedding_status = embedding_status
        self.embedding = embedding

    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'chunk_index': self.chunk_index,
            'embedding_status': self.embedding_status,
            'created_at': self.created_at.isoformat()
        }

class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    conversation_id = db.Column(db.String(255), nullable=True, index=True)
    question_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    answers = db.relationship('Answer', backref='question', lazy=True, cascade='all, delete-orphan')

    def __init__(self, user_id: int, question_text: str, conversation_id: str = None, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.question_text = question_text
        self.conversation_id = conversation_id

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'conversation_id': self.conversation_id,
            'question_text': self.question_text,
            'created_at': self.created_at.isoformat(),
            'answers': [a.to_dict() for a in self.answers]
        }

class Answer(db.Model):
    __tablename__ = 'answers'

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    answer_text = db.Column(db.Text, nullable=False)
    answer_source = db.Column(db.String(255), nullable=True) # e.g. "AI generated", "Manual"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, question_id: int, answer_text: str, answer_source: str = None, **kwargs):
        super().__init__(**kwargs)
        self.question_id = question_id
        self.answer_text = answer_text
        self.answer_source = answer_source

    def to_dict(self):
        return {
            'id': self.id,
            'question_id': self.question_id,
            'answer_text': self.answer_text,
            'answer_source': self.answer_source,
            'created_at': self.created_at.isoformat()
        }

class AuditLog(db.Model):
    # This might already exist in auth db, but we must use it safely
    __tablename__ = 'faq_audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True, index=True)
    action = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False) # success, failed
    ip_address = db.Column(db.String(45), nullable=True)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, action: str, status: str, user_id: int = None, ip_address: str = None, details: str = None, **kwargs):
        super().__init__(**kwargs)
        self.action = action
        self.status = status
        self.user_id = user_id
        self.ip_address = ip_address
        self.details = details
