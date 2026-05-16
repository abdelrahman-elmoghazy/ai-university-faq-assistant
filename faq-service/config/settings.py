import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost:5432/db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default_secret_key')
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5001))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    # ── Team Member 5 — AI Configuration ─────────────────────
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'mock')
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
    OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL', 'openai/gpt-3.5-turbo')
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3')

    # ── Team Member 5 — File Security ────────────────────────
    FILE_ENCRYPTION_KEY = os.getenv('FILE_ENCRYPTION_KEY', '')
    UPLOAD_DIR = os.getenv('UPLOAD_DIR', '/app/secure_uploads')
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '10'))
    MAX_CONTENT_LENGTH = MAX_FILE_SIZE_MB * 1024 * 1024  # Flask built-in

def get_config():
    return Config
