import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://auth_user:password@localhost:5432/auth_db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', 24))
    JWT_REFRESH_EXPIRATION_DAYS = int(os.getenv('JWT_REFRESH_EXPIRATION_DAYS', 7))

    # Server
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    TESTING = False
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))

    # OAuth
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:3000/auth/google/callback')

    GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID', '')
    GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET', '')
    GITHUB_REDIRECT_URI = os.getenv('GITHUB_REDIRECT_URI', 'http://localhost:3000/auth/github/callback')

    # Internal Service
    INTERNAL_API_KEY = os.getenv('INTERNAL_API_KEY')
    SERVICE_SECRET = os.getenv('SERVICE_SECRET')

    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', '/app/logs/auth.log')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    DEBUG = True
    # Provide testing secrets so tests run without requiring env files
    JWT_SECRET_KEY = 'test-secret'
    INTERNAL_API_KEY = 'test-internal'
    SERVICE_SECRET = 'test-service-secret'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

    @classmethod
    def validate(cls):
        """Fail fast if required production secrets are missing."""
        required_vars = ['JWT_SECRET_KEY', 'INTERNAL_API_KEY', 'SERVICE_SECRET']
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise RuntimeError(
                f"Missing required production environment variables: {', '.join(missing)}"
            )


def get_config():
    """Get configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'development')
    
    if env == 'production':
        ProductionConfig.validate()
        return ProductionConfig
    elif env == 'testing':
        return TestingConfig
    else:
        return DevelopmentConfig
