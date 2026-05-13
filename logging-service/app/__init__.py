"""
Logging Service — Flask App Factory
Receives structured audit logs and stores them in PostgreSQL.
"""
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "postgresql://admin:password@postgres:5432/faq_db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["INTERNAL_API_KEY"] = os.getenv("INTERNAL_API_KEY", "abc123secureinternalkey")

    db.init_app(app)
    CORS(app)

    with app.app_context():
        # Ensure tables exist
        from app.models.log_entry import LogEntry  # noqa: F401
        db.create_all()

        from app.routes.log_routes import logs_bp
        from app.routes.health_routes import health_bp

        app.register_blueprint(logs_bp)
        app.register_blueprint(health_bp)

    return app
