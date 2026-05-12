#!/usr/bin/env python3
"""
Utility script for Auth Service management
Includes commands for user creation, role assignment, etc.
"""

import sys
import argparse
from app import create_app
from app.models import db, User, Role, UserRole
from app.services.auth import AuthService
from app.services.rbac import RBACService


def create_admin_user(username, email, password, full_name=None):
    """Create an admin user"""
    app = create_app()
    
    with app.app_context():
        print(f"Creating admin user: {username}...")
        
        # Register user
        user, error = AuthService.register_user(username, email, password, full_name)
        if error:
            print(f"❌ Error: {error}")
            return False
        
        # Assign admin role
        admin_role = Role.query.filter_by(name='admin').first()
        user_role = UserRole.query.filter_by(user_id=user.id, role_id=admin_role.id)
        
        if user_role.first():
            print(f"⚠️  User already has admin role")
            return True
        
        # Remove default user role
        default_role = Role.query.filter_by(name='user').first()
        UserRole.query.filter_by(user_id=user.id, role_id=default_role.id).delete()
        
        # Assign admin role
        admin_user_role = UserRole(user_id=user.id, role_id=admin_role.id)
        db.session.add(admin_user_role)
        db.session.commit()
        
        print(f"✅ Admin user created successfully!")
        print(f"  Username: {username}")
        print(f"  Email: {email}")
        print(f"  Roles: admin")
        
        return True


def list_users():
    """List all users"""
    app = create_app()
    
    with app.app_context():
        users = User.query.all()
        
        if not users:
            print("No users found")
            return
        
        print(f"\n{'ID':<5} {'Username':<20} {'Email':<30} {'Roles':<20} {'Active':<8}")
        print("-" * 85)
        
        for user in users:
            roles = ', '.join([ur.role.name for ur in user.user_roles])
            print(f"{user.id:<5} {user.username:<20} {user.email:<30} {roles:<20} {str(user.is_active):<8}")


def list_roles():
    """List all roles"""
    app = create_app()
    
    with app.app_context():
        roles = Role.query.all()
        
        if not roles:
            print("No roles found")
            return
        
        print(f"\n{'ID':<5} {'Role':<20} {'Description':<50}")
        print("-" * 75)
        
        for role in roles:
            perms = len(role.role_permissions)
            desc = f"{role.description} ({perms} permissions)"
            print(f"{role.id:<5} {role.name:<20} {desc:<50}")


def assign_role(user_id, role_name):
    """Assign a role to a user"""
    app = create_app()
    
    with app.app_context():
        user = User.query.get(user_id)
        if not user:
            print(f"❌ User not found: {user_id}")
            return False
        
        success, message = RBACService.assign_role(user_id, role_name)
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
        
        return success


def main():
    """Main CLI handler"""
    parser = argparse.ArgumentParser(
        description='Auth Service Management Utility',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python manage.py create-admin --username admin --email admin@example.com --password AdminPass123!
  python manage.py list-users
  python manage.py list-roles
  python manage.py assign-role --user-id 1 --role admin
        '''
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Create admin command
    create_admin = subparsers.add_parser('create-admin', help='Create an admin user')
    create_admin.add_argument('--username', required=True, help='Username')
    create_admin.add_argument('--email', required=True, help='Email')
    create_admin.add_argument('--password', required=True, help='Password')
    create_admin.add_argument('--full-name', help='Full name')
    
    # List users command
    subparsers.add_parser('list-users', help='List all users')
    
    # List roles command
    subparsers.add_parser('list-roles', help='List all roles')
    
    # Assign role command
    assign = subparsers.add_parser('assign-role', help='Assign a role to a user')
    assign.add_argument('--user-id', type=int, required=True, help='User ID')
    assign.add_argument('--role', required=True, help='Role name')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'create-admin':
        create_admin_user(
            args.username,
            args.email,
            args.password,
            args.full_name
        )
    elif args.command == 'list-users':
        list_users()
    elif args.command == 'list-roles':
        list_roles()
    elif args.command == 'assign-role':
        assign_role(args.user_id, args.role)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)
