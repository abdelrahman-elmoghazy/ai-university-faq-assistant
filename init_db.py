#!/usr/bin/env python3
"""
Database initialization script
Initializes database schema and default data
"""

import os
import sys
from sqlalchemy import create_engine, text
from app.models import db, Role, Permission, RolePermission
from app import create_app


def init_database():
    """Initialize database with schema and default data"""
    app = create_app()
    
    with app.app_context():
        print("🔄 Initializing database...")
        
        # Create all tables
        print("  - Creating tables...")
        db.create_all()
        
        # Initialize default roles and permissions
        print("  - Creating roles...")
        roles_data = [
            ('admin', 'Administrator with full permissions'),
            ('user', 'Regular user'),
            ('moderator', 'Moderator with limited admin permissions')
        ]
        
        for role_name, description in roles_data:
            if not Role.query.filter_by(name=role_name).first():
                role = Role(name=role_name, description=description)
                db.session.add(role)
        
        db.session.commit()
        print("  ✓ Roles created")
        
        # Initialize permissions
        print("  - Creating permissions...")
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
        for perm_name, description in permissions_data:
            if not Permission.query.filter_by(name=perm_name).first():
                perm = Permission(name=perm_name, description=description)
                db.session.add(perm)
            permissions[perm_name] = Permission.query.filter_by(name=perm_name).first()
        
        db.session.commit()
        print("  ✓ Permissions created")
        
        # Assign permissions to roles
        print("  - Assigning permissions to roles...")
        admin_role = Role.query.filter_by(name='admin').first()
        user_role = Role.query.filter_by(name='user').first()
        
        admin_perms = [
            'manage_users', 'manage_roles', 'view_audit_logs',
            'manage_faq', 'upload_documents', 'view_own_data', 'download_documents'
        ]
        user_perms = ['view_own_data', 'upload_documents', 'download_documents']
        
        # Clear existing permissions
        RolePermission.query.filter_by(role_id=admin_role.id).delete()
        RolePermission.query.filter_by(role_id=user_role.id).delete()
        
        # Assign admin permissions
        for perm_name in admin_perms:
            if perm_name in permissions:
                rp = RolePermission(role_id=admin_role.id, permission_id=permissions[perm_name].id)
                db.session.add(rp)
        
        # Assign user permissions
        for perm_name in user_perms:
            if perm_name in permissions:
                rp = RolePermission(role_id=user_role.id, permission_id=permissions[perm_name].id)
                db.session.add(rp)
        
        db.session.commit()
        print("  ✓ Permissions assigned")
        
        print("\n✅ Database initialized successfully!")
        print("\n📋 Summary:")
        print(f"  - Roles: {len(roles_data)}")
        print(f"  - Permissions: {len(permissions_data)}")
        print(f"  - Tables: 7")


if __name__ == '__main__':
    try:
        init_database()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)
