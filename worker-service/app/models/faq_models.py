import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    title = Column(String(255))
    file_name = Column(String(255))
    file_path = Column(String(500))
    upload_status = Column(String(50))
    uploaded_by = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class Chunk(Base):
    __tablename__ = 'chunks'

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('documents.id'))
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    from pgvector.sqlalchemy import Vector
    embedding = Column(Vector(384))
    embedding_status = Column(String(50), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
