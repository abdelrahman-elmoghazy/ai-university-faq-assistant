import jwt
import logging
from functools import wraps
from flask import request, jsonify, current_app
from typing import Optional

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

def verify_token(token: str):
    try:
        payload = jwt.decode(
            token,
            current_app.config['JWT_SECRET_KEY'],
            algorithms=[current_app.config.get('JWT_ALGORITHM', 'HS256')]
        )
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "Token has expired"
    except jwt.InvalidTokenError as e:
        return None, f"Invalid token: {str(e)}"
    except Exception as e:
        return None, "Authentication failed"

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_header()
        
        if not token:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Missing or invalid authorization header'
            }), 401

        payload, error = verify_token(token)
        
        if error:
            return jsonify({
                'error': 'Unauthorized',
                'message': error
            }), 401

        request.user_id = payload.get('user_id')
        request.username = payload.get('username')
        request.roles = payload.get('roles', [])
        
        return f(*args, **kwargs)
    
    return decorated

def get_client_ip() -> str:
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr or '0.0.0.0'
