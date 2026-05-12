import jwt
import bcrypt
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from typing import Optional, Dict, Any, Tuple

from app.models import User, Role, UserRole, LoginAttempt, AuditLog, db

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification error: {str(e)}")
            return False

    @staticmethod
    def register_user(username: str, email: str, password: str, full_name: Optional[str] = None) -> Tuple[Optional[User], Optional[str]]:
        """Register a new user"""
        try:
            # Check if user already exists
            if User.query.filter_by(username=username).first():
                return None, "Username already exists"
            
            if User.query.filter_by(email=email).first():
                return None, "Email already exists"

            # Create user with hashed password
            user = User(
                username=username,
                email=email,
                password_hash=AuthService.hash_password(password),
                full_name=full_name
            )

            # Add default USER role
            user_role = UserRole(user=user, role=Role.query.filter_by(name='user').first())

            db.session.add(user)
            db.session.add(user_role)
            db.session.commit()

            logger.info(f"User registered: {username}")
            return user, None

        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {str(e)}")
            return None, f"Registration failed: {str(e)}"

    @staticmethod
    def login_user(email: str, password: str, ip_address: str = None, user_agent: str = None) -> Tuple[Optional[User], Optional[str]]:
        """Authenticate user"""
        try:
            user = User.query.filter_by(email=email).first()

            if not user:
                # Log failed login attempt
                AuthService._log_login_attempt(
                    email=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False,
                    reason="user_not_found"
                )
                return None, "Invalid email or password"

            if not user.is_active:
                AuthService._log_login_attempt(
                    user_id=user.id,
                    email=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False,
                    reason="user_inactive"
                )
                return None, "User account is inactive"

            if not AuthService.verify_password(password, user.password_hash):
                AuthService._log_login_attempt(
                    user_id=user.id,
                    email=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False,
                    reason="invalid_password"
                )
                return None, "Invalid email or password"

            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()

            AuthService._log_login_attempt(
                user_id=user.id,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True
            )

            logger.info(f"User logged in: {email}")
            return user, None

        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return None, f"Login failed: {str(e)}"

    @staticmethod
    def _log_login_attempt(user_id: int = None, email: str = None, ip_address: str = None, 
                          user_agent: str = None, success: bool = False, reason: str = None):
        """Log login attempt"""
        try:
            attempt = LoginAttempt(
                user_id=user_id,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                reason=reason
            )
            db.session.add(attempt)
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to log login attempt: {str(e)}")

    @staticmethod
    def generate_tokens(user: User) -> Dict[str, Any]:
        """Generate JWT tokens"""
        now = datetime.utcnow()
        
        # Get user roles
        roles = [ur.role.name for ur in user.user_roles]
        
        # Access token payload
        access_payload = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'roles': roles,
            'iat': now,
            'exp': now + timedelta(hours=current_app.config['JWT_EXPIRATION_HOURS']),
            'type': 'access'
        }

        # Refresh token payload
        refresh_payload = {
            'user_id': user.id,
            'iat': now,
            'exp': now + timedelta(days=current_app.config['JWT_REFRESH_EXPIRATION_DAYS']),
            'type': 'refresh'
        }

        access_token = jwt.encode(
            access_payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm=current_app.config['JWT_ALGORITHM']
        )

        refresh_token = jwt.encode(
            refresh_payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm=current_app.config['JWT_ALGORITHM']
        )

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': current_app.config['JWT_EXPIRATION_HOURS'] * 3600,
            'token_type': 'Bearer'
        }

    @staticmethod
    def verify_token(token: str) -> Tuple[Optional[Dict], Optional[str]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=[current_app.config['JWT_ALGORITHM']]
            )
            return payload, None
        except jwt.ExpiredSignatureError:
            return None, "Token has expired"
        except jwt.InvalidTokenError:
            return None, "Invalid token"
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            return None, "Token verification failed"

    @staticmethod
    def refresh_access_token(refresh_token: str) -> Tuple[Optional[str], Optional[str]]:
        """Generate new access token from refresh token"""
        payload, error = AuthService.verify_token(refresh_token)

        if error or payload.get('type') != 'refresh':
            return None, "Invalid refresh token"

        user = User.query.get(payload['user_id'])
        if not user or not user.is_active:
            return None, "User not found or inactive"

        tokens = AuthService.generate_tokens(user)
        return tokens['access_token'], None

    @staticmethod
    def logout_user(user_id: int, ip_address: str = None, user_agent: str = None):
        """Logout user (log audit)"""
        try:
            user = User.query.get(user_id)
            if user:
                audit = AuditLog(
                    user_id=user_id,
                    action='logout',
                    resource_type='auth',
                    status='success',
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                db.session.add(audit)
                db.session.commit()
                logger.info(f"User logged out: {user.email}")
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")

    @staticmethod
    def log_audit(user_id: int = None, action: str = None, resource_type: str = None, 
                 resource_id: str = None, status: str = None, details: Dict = None,
                 ip_address: str = None, user_agent: str = None):
        """Log audit event"""
        try:
            audit = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                status=status,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.session.add(audit)
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to log audit: {str(e)}")
