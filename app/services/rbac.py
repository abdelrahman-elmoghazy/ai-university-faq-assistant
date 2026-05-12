import logging
from typing import List, Optional
from app.models import User, Role, Permission, UserRole, RolePermission, db

logger = logging.getLogger(__name__)


class RBACService:
    """Role-Based Access Control service"""

    @staticmethod
    def get_user_roles(user_id: int) -> List[str]:
        """Get all roles for a user"""
        try:
            user_roles = UserRole.query.filter_by(user_id=user_id).all()
            return [ur.role.name for ur in user_roles]
        except Exception as e:
            logger.error(f"Error getting user roles: {str(e)}")
            return []

    @staticmethod
    def get_user_permissions(user_id: int) -> List[str]:
        """Get all permissions for a user"""
        try:
            user_roles = UserRole.query.filter_by(user_id=user_id).all()
            permissions = set()
            
            for ur in user_roles:
                role_permissions = RolePermission.query.filter_by(role_id=ur.role_id).all()
                for rp in role_permissions:
                    permissions.add(rp.permission.name)
            
            return list(permissions)
        except Exception as e:
            logger.error(f"Error getting user permissions: {str(e)}")
            return []

    @staticmethod
    def has_role(user_id: int, role_name: str) -> bool:
        """Check if user has a specific role"""
        try:
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                return False

            user_role = UserRole.query.filter_by(user_id=user_id, role_id=role.id).first()
            return user_role is not None
        except Exception as e:
            logger.error(f"Error checking role: {str(e)}")
            return False

    @staticmethod
    def has_permission(user_id: int, permission_name: str) -> bool:
        """Check if user has a specific permission"""
        try:
            user_permissions = RBACService.get_user_permissions(user_id)
            return permission_name in user_permissions
        except Exception as e:
            logger.error(f"Error checking permission: {str(e)}")
            return False

    @staticmethod
    def assign_role(user_id: int, role_name: str, assigned_by: int = None) -> tuple:
        """Assign a role to a user"""
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"

            role = Role.query.filter_by(name=role_name).first()
            if not role:
                return False, f"Role '{role_name}' not found"

            # Check if already has role
            existing = UserRole.query.filter_by(user_id=user_id, role_id=role.id).first()
            if existing:
                return False, "User already has this role"

            user_role = UserRole(
                user_id=user_id,
                role_id=role.id,
                assigned_by=assigned_by
            )

            db.session.add(user_role)
            db.session.commit()

            logger.info(f"Role '{role_name}' assigned to user {user_id}")
            return True, f"Role '{role_name}' assigned successfully"

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error assigning role: {str(e)}")
            return False, str(e)

    @staticmethod
    def revoke_role(user_id: int, role_name: str) -> tuple:
        """Revoke a role from a user"""
        try:
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                return False, f"Role '{role_name}' not found"

            user_role = UserRole.query.filter_by(user_id=user_id, role_id=role.id).first()
            if not user_role:
                return False, "User does not have this role"

            db.session.delete(user_role)
            db.session.commit()

            logger.info(f"Role '{role_name}' revoked from user {user_id}")
            return True, f"Role '{role_name}' revoked successfully"

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error revoking role: {str(e)}")
            return False, str(e)

    @staticmethod
    def create_role(role_name: str, description: str = None) -> tuple:
        """Create a new role"""
        try:
            existing = Role.query.filter_by(name=role_name).first()
            if existing:
                return False, f"Role '{role_name}' already exists"

            role = Role(name=role_name, description=description)
            db.session.add(role)
            db.session.commit()

            logger.info(f"Role '{role_name}' created")
            return True, role

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating role: {str(e)}")
            return False, str(e)

    @staticmethod
    def create_permission(permission_name: str, description: str = None) -> tuple:
        """Create a new permission"""
        try:
            existing = Permission.query.filter_by(name=permission_name).first()
            if existing:
                return False, f"Permission '{permission_name}' already exists"

            permission = Permission(name=permission_name, description=description)
            db.session.add(permission)
            db.session.commit()

            logger.info(f"Permission '{permission_name}' created")
            return True, permission

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating permission: {str(e)}")
            return False, str(e)

    @staticmethod
    def assign_permission_to_role(role_name: str, permission_name: str) -> tuple:
        """Assign a permission to a role"""
        try:
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                return False, f"Role '{role_name}' not found"

            permission = Permission.query.filter_by(name=permission_name).first()
            if not permission:
                return False, f"Permission '{permission_name}' not found"

            existing = RolePermission.query.filter_by(role_id=role.id, permission_id=permission.id).first()
            if existing:
                return False, f"Permission already assigned to role"

            role_permission = RolePermission(role_id=role.id, permission_id=permission.id)
            db.session.add(role_permission)
            db.session.commit()

            logger.info(f"Permission '{permission_name}' assigned to role '{role_name}'")
            return True, "Permission assigned successfully"

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error assigning permission: {str(e)}")
            return False, str(e)

    @staticmethod
    def revoke_permission_from_role(role_name: str, permission_name: str) -> tuple:
        """Revoke a permission from a role"""
        try:
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                return False, f"Role '{role_name}' not found"

            permission = Permission.query.filter_by(name=permission_name).first()
            if not permission:
                return False, f"Permission '{permission_name}' not found"

            role_permission = RolePermission.query.filter_by(role_id=role.id, permission_id=permission.id).first()
            if not role_permission:
                return False, f"Permission not assigned to role"

            db.session.delete(role_permission)
            db.session.commit()

            logger.info(f"Permission '{permission_name}' revoked from role '{role_name}'")
            return True, "Permission revoked successfully"

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error revoking permission: {str(e)}")
            return False, str(e)
