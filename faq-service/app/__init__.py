from flask import Flask
from flask_cors import CORS
import logging
from config.settings import get_config
from app.models.faq_models import db

def create_app():
    app = Flask(__name__)
    config = get_config()
    app.config.from_object(config)
    
    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})
    
    logging.basicConfig(level=getattr(logging, app.config['LOG_LEVEL'], 'INFO'),
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    with app.app_context():
        db.create_all()
        
        # FAQ routes (Member 3/4 — preserved)
        from app.routes.faq_routes import faq_bp
        app.register_blueprint(faq_bp, url_prefix='/api/faq')

        # File upload routes (Team Member 5)
        from app.routes.file_routes import file_bp
        app.register_blueprint(file_bp, url_prefix='/api/files')

        # Admin dashboard routes (Team Member 5)
        from app.routes.admin_routes import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/api/admin')
        
        @app.route('/health', methods=['GET'])
        def health():
            return {'status': 'healthy', 'service': 'FAQ Service'}, 200

    return app
