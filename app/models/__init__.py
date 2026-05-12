from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum

db = SQLAlchemy()


class RoleEnum(Enum):
    """Role enum"""
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"


class User(db.Model):
    """User model"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_verified = db.Column(db.Boolean, default=False)
    oauth_provider = db.Column(db.String(50), nullable=True)  # google, github
    oauth_id = db.Column(db.String(255), nullable=True, unique=True)
    profile_picture = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    # Relationships
    user_roles = db.relationship(
        'UserRole',
        foreign_keys='UserRole.user_id',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan'
    )
    login_attempts = db.relationship('LoginAttempt', backref='user', lazy=True, cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'profile_picture': self.profile_picture,
            'roles': [ur.role.name for ur in self.user_roles],
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class Role(db.Model):
    """Role model"""
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user_roles = db.relationship('UserRole', backref='role', lazy=True, cascade='all, delete-orphan')
    role_permissions = db.relationship('RolePermission', backref='role', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Role {self.name}>'


class Permission(db.Model):
    """Permission model"""
    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    role_permissions = db.relationship('RolePermission', backref='permission', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Permission {self.name}>'


class UserRole(db.Model):
    """User-Role association model"""
    __tablename__ = 'user_roles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    __table_args__ = (db.UniqueConstraint('user_id', 'role_id', name='_user_role_uc'),)

    def __repr__(self):
        return f'<UserRole user_id={self.user_id} role_id={self.role_id}>'


class RolePermission(db.Model):
    """Role-Permission association model"""
    __tablename__ = 'role_permissions'

    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('role_id', 'permission_id', name='_role_permission_uc'),)

    def __repr__(self):
        return f'<RolePermission role_id={self.role_id} permission_id={self.permission_id}>'


class LoginAttempt(db.Model):
    """Login attempt tracking for security"""
    __tablename__ = 'login_attempts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    email = db.Column(db.String(120), index=True)
    ip_address = db.Column(db.String(45))  # IPv6 support
    user_agent = db.Column(db.String(500))
    success = db.Column(db.Boolean, default=False)
    reason = db.Column(db.String(255), nullable=True)  # e.g., 'invalid_password', 'user_not_found'
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<LoginAttempt {self.email} at {self.attempted_at}>'


class AuditLog(db.Model):
    """Audit log for tracking user actions"""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    resource_type = db.Column(db.String(50))  # e.g., 'user', 'document', 'admin'
    resource_id = db.Column(db.String(50))
    status = db.Column(db.String(20))  # success, failed
    details = db.Column(db.JSON)  # Additional context
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<AuditLog {self.action} by user {self.user_id}>'
