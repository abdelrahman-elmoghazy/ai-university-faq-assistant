import logging
from flask import Blueprint, request, jsonify
from app.schemas.user import (
    UserRegisterRequest, UserLoginRequest, TokenRefreshRequest,
    ChangePasswordRequest, GoogleTokenRequest, GitHubTokenRequest
)
from app.services.auth import AuthService
from app.services.oauth import GoogleOAuthService, GitHubOAuthService
from app.services.rbac import RBACService
from app.middleware.auth_middleware import (
    token_required, get_client_ip, get_user_agent, 
    admin_required, internal_service_auth_required
)
from app.models import User, db
from app.services.event_publisher import publish_auth_event

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        # Validate request
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Request body is empty'
            }), 400

        # Parse and validate request
        try:
            req = UserRegisterRequest(**data)
        except Exception as e:
            return jsonify({
                'error': 'Validation Error',
                'message': str(e)
            }), 422

        # Register user
        user, error = AuthService.register_user(
            username=req.username,
            email=req.email,
            password=req.password,
            full_name=req.full_name
        )

        if error:
            # Log failed registration
            AuthService.log_audit(
                action='registration_failed',
                resource_type='user',
                status='failed',
                details={'reason': error, 'email': req.email},
                ip_address=get_client_ip(),
                user_agent=get_user_agent()
            )
            return jsonify({
                'error': 'Registration Failed',
                'message': error
            }), 400

        # Log successful registration
        AuthService.log_audit(
            user_id=user.id,
            action='registration',
            resource_type='user',
            status='success',
            details={'username': user.username},
            ip_address=get_client_ip(),
            user_agent=get_user_agent()
        )

        # Publish to RabbitMQ
        publish_auth_event("auth.register", {
            "user_id":    user.id,
            "email":      user.email,
            "username":   user.username,
            "ip_address": get_client_ip(),
        })

        return jsonify({
            'message': 'Registration successful',
            'user': user.to_dict()
        }), 201

    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        # Validate request
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Request body is empty'
            }), 400

        # Parse and validate request
        try:
            req = UserLoginRequest(**data)
        except Exception as e:
            return jsonify({
                'error': 'Validation Error',
                'message': str(e)
            }), 422

        # Authenticate user
        user, error = AuthService.login_user(
            email=req.email,
            password=req.password,
            ip_address=get_client_ip(),
            user_agent=get_user_agent()
        )

        if error:
            publish_auth_event("auth.login.failed", {
                "email":      req.email,
                "ip_address": get_client_ip(),
                "reason":     error,
            })
            return jsonify({
                'error': 'Authentication Failed',
                'message': error
            }), 401

        # Generate tokens
        tokens = AuthService.generate_tokens(user)

        publish_auth_event("auth.login.success", {
            "user_id":    user.id,
            "email":      user.email,
            "ip_address": get_client_ip(),
            "user_agent": get_user_agent(),
        })

        return jsonify({
            'message': 'Login successful',
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'token_type': tokens['token_type'],
            'expires_in': tokens['expires_in'],
            'user': user.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """Refresh JWT token endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Request body is empty'
            }), 400

        try:
            req = TokenRefreshRequest(**data)
        except Exception as e:
            return jsonify({
                'error': 'Validation Error',
                'message': str(e)
            }), 422

        access_token, error = AuthService.refresh_access_token(req.refresh_token)

        if error:
            return jsonify({
                'error': 'Token Refresh Failed',
                'message': error
            }), 401

        return jsonify({
            'access_token': access_token,
            'token_type': 'Bearer'
        }), 200

    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500


@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    """User logout endpoint"""
    try:
        AuthService.logout_user(
            user_id=request.user_id,
            ip_address=get_client_ip(),
            user_agent=get_user_agent()
        )

        publish_auth_event("auth.logout", {
            "user_id":    request.user_id,
            "ip_address": get_client_ip(),
        })

        return jsonify({
            'message': 'Logout successful'
        }), 200

    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user():
    """Get current user info"""
    try:
        user = User.query.get(request.user_id)

        if not user:
            return jsonify({
                'error': 'Not Found',
                'message': 'User not found'
            }), 404

        return jsonify({
            'user': user.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500


@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password():
    """Change password endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Request body is empty'
            }), 400

        try:
            req = ChangePasswordRequest(**data)
        except Exception as e:
            return jsonify({
                'error': 'Validation Error',
                'message': str(e)
            }), 422

        user = User.query.get(request.user_id)

        if not user:
            return jsonify({
                'error': 'Not Found',
                'message': 'User not found'
            }), 404

        # Verify old password
        if not AuthService.verify_password(req.old_password, user.password_hash):
            return jsonify({
                'error': 'Validation Error',
                'message': 'Old password is incorrect'
            }), 422

        # Update password
        user.password_hash = AuthService.hash_password(req.new_password)
        db.session.commit()

        AuthService.log_audit(
            user_id=request.user_id,
            action='change_password',
            resource_type='user',
            status='success',
            ip_address=get_client_ip(),
            user_agent=get_user_agent()
        )

        return jsonify({
            'message': 'Password changed successfully'
        }), 200

    except Exception as e:
        logger.error(f"Change password error: {str(e)}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500


@auth_bp.route('/oauth/google', methods=['POST'])
def google_oauth_callback():
    """Google OAuth callback"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Request body is empty'
            }), 400

        try:
            req = GoogleTokenRequest(**data)
        except Exception as e:
            return jsonify({
                'error': 'Validation Error',
                'message': str(e)
            }), 422

        # Get user info from Google
        user_info, error = GoogleOAuthService.get_user_info(req.access_token)

        if error:
            return jsonify({
                'error': 'OAuth Error',
                'message': error
            }), 400

        # Authenticate or create user
        user, error = GoogleOAuthService.authenticate_or_create_user(user_info)

        if error:
            return jsonify({
                'error': 'Authentication Error',
                'message': error
            }), 400

        # Generate tokens
        tokens = AuthService.generate_tokens(user)

        AuthService.log_audit(
            user_id=user.id,
            action='oauth_login',
            resource_type='auth',
            details={'provider': 'google'},
            status='success',
            ip_address=get_client_ip(),
            user_agent=get_user_agent()
        )

        return jsonify({
            'message': 'Google OAuth login successful',
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'token_type': tokens['token_type'],
            'expires_in': tokens['expires_in'],
            'user': user.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Google OAuth error: {str(e)}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500


@auth_bp.route('/oauth/github', methods=['POST'])
def github_oauth_callback():
    """GitHub OAuth callback"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Request body is empty'
            }), 400

        try:
            req = GitHubTokenRequest(**data)
        except Exception as e:
            return jsonify({
                'error': 'Validation Error',
                'message': str(e)
            }), 422

        # 1. Exchange code for access token
        access_token, error = GitHubOAuthService.exchange_code_for_token(req.code)
        
        if error:
            return jsonify({
                'error': 'OAuth Error',
                'message': error
            }), 400

        # 2. Get user info from GitHub using the token
        user_info, error = GitHubOAuthService.get_user_info(access_token)

        if error:
            return jsonify({
                'error': 'OAuth Error',
                'message': error
            }), 400

        # Authenticate or create user
        user, error = GitHubOAuthService.authenticate_or_create_user(user_info)

        if error:
            return jsonify({
                'error': 'Authentication Error',
                'message': error
            }), 400

        # Generate tokens
        tokens = AuthService.generate_tokens(user)

        AuthService.log_audit(
            user_id=user.id,
            action='oauth_login',
            resource_type='auth',
            details={'provider': 'github'},
            status='success',
            ip_address=get_client_ip(),
            user_agent=get_user_agent()
        )

        return jsonify({
            'message': 'GitHub OAuth login successful',
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'token_type': tokens['token_type'],
            'expires_in': tokens['expires_in'],
            'user': user.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"GitHub OAuth error: {str(e)}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500
