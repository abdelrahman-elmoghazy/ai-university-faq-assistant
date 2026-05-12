import logging
from flask import Blueprint, request, jsonify
from app.services.rbac import RBACService
from app.services.auth import AuthService
from app.middleware.auth_middleware import (
    admin_required, get_client_ip, get_user_agent
)
from app.models import User, db

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_all_users():
    """Get all users (admin only)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        pagination = User.query.paginate(page=page, per_page=per_page)

        users = [user.to_dict() for user in pagination.items]

        return jsonify({
            'users': users,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }), 200

    except Exception as e:
        logger.error(f"Get users error: {str(e)}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500


@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    """Get user details (admin only)"""
    try:
        user = User.query.get(user_id)

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


@admin_bp.route('/users/<int:user_id>/roles', methods=['POST'])
@admin_required
def assign_role(user_id):
    """Assign role to user (admin only)"""
    try:
        if user_id == request.user_id:
            return jsonify({
                'error': 'Forbidden',
                'message': 'Cannot modify own role'
            }), 403

        data = request.get_json()

        if not data or 'role' not in data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Role name is required'
            }), 400

        role_name = data.get('role')

        success, message = RBACService.assign_role(
            user_id=user_id,
            role_name=role_name,
            assigned_by=request.user_id
        )

        if not success:
            return jsonify({
                'error': 'Failed',
                'message': message
            }), 400

        user = User.query.get(user_id)

        AuthService.log_audit(
            user_id=request.user_id,
            action='assign_role',
            resource_type='user',
            resource_id=str(user_id),
            status='success',
            details={'role': role_name, 'target_user': user.username},
            ip_address=get_client_ip(),
            user_agent=get_user_agent()
        )

        return jsonify({
            'message': message,
            'user': user.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Assign role error: {str(e)}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500


@admin_bp.route('/users/<int:user_id>/roles/<role_name>', methods=['DELETE'])
@admin_required
def revoke_role(user_id, role_name):
    """Revoke role from user (admin only)"""
    try:
        if user_id == request.user_id:
            return jsonify({
                'error': 'Forbidden',
                'message': 'Cannot modify own role'
            }), 403

        success, message = RBACService.revoke_role(
            user_id=user_id,
            role_name=role_name
        )

        if not success:
            return jsonify({
                'error': 'Failed',
                'message': message
            }), 400

        user = User.query.get(user_id)

        AuthService.log_audit(
            user_id=request.user_id,
            action='revoke_role',
            resource_type='user',
            resource_id=str(user_id),
            status='success',
            details={'role': role_name, 'target_user': user.username},
            ip_address=get_client_ip(),
            user_agent=get_user_agent()
        )

        return jsonify({
            'message': message,
            'user': user.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Revoke role error: {str(e)}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500


@admin_bp.route('/users/<int:user_id>/status', methods=['PATCH'])
@admin_required
def update_user_status(user_id):
    """Update user active status (admin only)"""
    try:
        data = request.get_json()

        if not data or 'is_active' not in data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'is_active is required'
            }), 400

        user = User.query.get(user_id)

        if not user:
            return jsonify({
                'error': 'Not Found',
                'message': 'User not found'
            }), 404

        old_status = user.is_active
        user.is_active = data.get('is_active')
        db.session.commit()

        AuthService.log_audit(
            user_id=request.user_id,
            action='update_user_status',
            resource_type='user',
            resource_id=str(user_id),
            status='success',
            details={'username': user.username, 'old_status': old_status, 'new_status': user.is_active},
            ip_address=get_client_ip(),
            user_agent=get_user_agent()
        )

        return jsonify({
            'message': 'User status updated',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Update user status error: {str(e)}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500
