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
        
        from app.routes.faq_routes import faq_bp
        app.register_blueprint(faq_bp, url_prefix='/api/faq')
        
        @app.route('/health', methods=['GET'])
        def health():
            return {'status': 'healthy', 'service': 'FAQ Service'}, 200

    return app
