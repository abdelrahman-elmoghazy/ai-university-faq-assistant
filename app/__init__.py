from flask import Flask
from flask_cors import CORS
from config.settings import get_config
from app.models import db
import logging
import os

def create_app():
    """Application factory"""
    app = Flask(__name__)
    
    # Load configuration
    config = get_config()
    app.config.from_object(config)
    
    # Initialize database
    db.init_app(app)
    
    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})
    
    # Setup logging
    setup_logging(app)
    
    with app.app_context():
        # Create database tables
        db.create_all()
        
        # Initialize default roles and permissions
        initialize_default_roles_and_permissions()
        
        # Register blueprints
        from app.routes.auth_routes import auth_bp
        from app.routes.admin_routes import admin_bp
        
        app.register_blueprint(auth_bp)
        app.register_blueprint(admin_bp)
        
        # Health check endpoint
        @app.route('/health', methods=['GET'])
        def health():
            return {'status': 'healthy'}, 200
        
        # Root endpoint
        @app.route('/', methods=['GET'])
        def root():
            return {
                'service': 'Auth Service',
                'version': '1.0.0',
                'status': 'running'
            }, 200
    
    return app


def setup_logging(app):
    """Setup logging"""
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    log_file = app.config.get('LOG_FILE', '/app/logs/auth.log')
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


def initialize_default_roles_and_permissions():
    """Initialize default roles and permissions"""
    from app.models import Role, Permission, RolePermission
    
    # Create default roles
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        admin_role = Role(name='admin', description='Administrator role with full permissions')
        db.session.add(admin_role)
    
    user_role = Role.query.filter_by(name='user').first()
    if not user_role:
        user_role = Role(name='user', description='Regular user role')
        db.session.add(user_role)
    
    moderator_role = Role.query.filter_by(name='moderator').first()
    if not moderator_role:
        moderator_role = Role(name='moderator', description='Moderator role')
        db.session.add(moderator_role)
    
    db.session.commit()
    
    # Create default permissions
    permissions_data = [
        ('manage_users', 'Manage all users'),
        ('manage_roles', 'Manage roles and permissions'),
        ('view_audit_logs', 'View audit logs'),
        ('manage_faq', 'Manage FAQ content'),
        ('upload_documents', 'Upload documents'),
        ('view_own_data', 'View own data'),
        ('download_documents', 'Download documents'),
    ]
    
    permissions = {}
    for perm_name, perm_desc in permissions_data:
        perm = Permission.query.filter_by(name=perm_name).first()
        if not perm:
            perm = Permission(name=perm_name, description=perm_desc)
            db.session.add(perm)
        permissions[perm_name] = perm
    
    db.session.commit()
    
    # Assign permissions to roles
    admin_perms = ['manage_users', 'manage_roles', 'view_audit_logs', 'manage_faq', 'upload_documents', 'view_own_data', 'download_documents']
    user_perms = ['view_own_data', 'upload_documents', 'download_documents']
    
    # Clear existing permissions first
    RolePermission.query.filter_by(role_id=admin_role.id).delete()
    RolePermission.query.filter_by(role_id=user_role.id).delete()
    
    for perm_name in admin_perms:
        if perm_name in permissions:
            rp = RolePermission.query.filter_by(role_id=admin_role.id, permission_id=permissions[perm_name].id).first()
            if not rp:
                rp = RolePermission(role_id=admin_role.id, permission_id=permissions[perm_name].id)
                db.session.add(rp)
    
    for perm_name in user_perms:
        if perm_name in permissions:
            rp = RolePermission.query.filter_by(role_id=user_role.id, permission_id=permissions[perm_name].id).first()
            if not rp:
                rp = RolePermission(role_id=user_role.id, permission_id=permissions[perm_name].id)
                db.session.add(rp)
    
    db.session.commit()
