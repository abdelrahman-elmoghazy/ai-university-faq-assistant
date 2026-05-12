import logging
from functools import wraps
from flask import request, jsonify, current_app
from typing import Optional, Dict

from app.services.auth import AuthService
from app.services.rbac import RBACService
from app.models import User

logger = logging.getLogger(__name__)


def get_token_from_header() -> Optional[str]:
    """Extract JWT token from Authorization header"""
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header:
        return None
    
    try:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == 'bearer':
            return parts[1]
    except Exception as e:
        logger.error(f"Error parsing auth header: {str(e)}")
    
    return None


def get_client_ip() -> str:
    """Get client IP address from request"""
    # Check for proxy headers first
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    
    return request.remote_addr or '0.0.0.0'


def get_user_agent() -> str:
    """Get user agent from request"""
    return request.headers.get('User-Agent', 'Unknown')


def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_header()
        
        if not token:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Missing or invalid authorization header'
            }), 401

        payload, error = AuthService.verify_token(token)
        
        if error:
            return jsonify({
                'error': 'Unauthorized',
                'message': error
            }), 401

        # Store payload in request context
        request.user_id = payload.get('user_id')
        request.username = payload.get('username')
        request.email = payload.get('email')
        request.roles = payload.get('roles', [])
        
        return f(*args, **kwargs)
    
    return decorated


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_header()
        
        if not token:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Missing or invalid authorization header'
            }), 401

        payload, error = AuthService.verify_token(token)
        
        if error:
            return jsonify({
                'error': 'Unauthorized',
                'message': error
            }), 401

        # Check if user has admin role
        if 'admin' not in payload.get('roles', []):
            return jsonify({
                'error': 'Forbidden',
                'message': 'Admin role required'
            }), 403

        request.user_id = payload.get('user_id')
        request.username = payload.get('username')
        request.email = payload.get('email')
        request.roles = payload.get('roles', [])
        
        return f(*args, **kwargs)
    
    return decorated


def internal_service_auth_required(f):
    """Decorator to require internal service authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check for internal API key
        api_key = request.headers.get('X-Internal-API-Key')
        
        if not api_key:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Missing internal API key'
            }), 401

        if api_key != current_app.config['INTERNAL_API_KEY']:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Invalid internal API key'
            }), 401

        return f(*args, **kwargs)
    
    return decorated


def require_permission(permission_name: str):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = get_token_from_header()
            
            if not token:
                return jsonify({
                    'error': 'Unauthorized',
                    'message': 'Missing or invalid authorization header'
                }), 401

            payload, error = AuthService.verify_token(token)
            
            if error:
                return jsonify({
                    'error': 'Unauthorized',
                    'message': error
                }), 401

            user_id = payload.get('user_id')
            
            # Check permission
            if not RBACService.has_permission(user_id, permission_name):
                return jsonify({
                    'error': 'Forbidden',
                    'message': f'Permission "{permission_name}" required'
                }), 403

            request.user_id = user_id
            request.username = payload.get('username')
            request.email = payload.get('email')
            request.roles = payload.get('roles', [])
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator


def require_role(role_name: str):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = get_token_from_header()
            
            if not token:
                return jsonify({
                    'error': 'Unauthorized',
                    'message': 'Missing or invalid authorization header'
                }), 401

            payload, error = AuthService.verify_token(token)
            
            if error:
                return jsonify({
                    'error': 'Unauthorized',
                    'message': error
                }), 401

            # Check role
            if role_name not in payload.get('roles', []):
                return jsonify({
                    'error': 'Forbidden',
                    'message': f'Role "{role_name}" required'
                }), 403

            request.user_id = payload.get('user_id')
            request.username = payload.get('username')
            request.email = payload.get('email')
            request.roles = payload.get('roles', [])
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator
