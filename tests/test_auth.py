import unittest
from app import create_app
from app.models import db, User, Role, Permission, UserRole, RolePermission
from config.settings import TestingConfig
import os


class AuthServiceTestCase(unittest.TestCase):
    """Base test case class"""

    def setUp(self):
        """Set up test client and database"""
        os.environ['FLASK_ENV'] = 'testing'
        self.app = create_app()
        self.app.config.from_object(TestingConfig)
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            self._seed_database()

    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _seed_database(self):
        """Seed database with test data"""
        # Reuse default roles/permissions if the app factory already created them.
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(name='admin', description='Admin')
            db.session.add(admin_role)

        user_role = Role.query.filter_by(name='user').first()
        if not user_role:
            user_role = Role(name='user', description='User')
            db.session.add(user_role)

        perm1 = Permission.query.filter_by(name='manage_users').first()
        if not perm1:
            perm1 = Permission(name='manage_users', description='Manage users')
            db.session.add(perm1)

        perm2 = Permission.query.filter_by(name='view_own_data').first()
        if not perm2:
            perm2 = Permission(name='view_own_data', description='View own data')
            db.session.add(perm2)

        db.session.commit()

        # Reset role-permission links for a clean and repeatable test state.
        RolePermission.query.delete()
        db.session.commit()

        # Assign permissions
        rp1 = RolePermission(role_id=admin_role.id, permission_id=perm1.id)
        rp2 = RolePermission(role_id=user_role.id, permission_id=perm2.id)
        
        db.session.add_all([rp1, rp2])
        db.session.commit()


class RegistrationTestCase(AuthServiceTestCase):
    """Registration tests"""

    def test_valid_registration(self):
        """Test valid user registration"""
        response = self.client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'full_name': 'Test User'
        })
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn('user', data)
        self.assertEqual(data['user']['username'], 'testuser')
        self.assertEqual(data['user']['email'], 'test@example.com')

    def test_duplicate_email(self):
        """Test registration with duplicate email"""
        # First registration
        self.client.post('/api/auth/register', json={
            'username': 'testuser1',
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'full_name': 'Test User 1'
        })

        # Second registration with same email
        response = self.client.post('/api/auth/register', json={
            'username': 'testuser2',
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'full_name': 'Test User 2'
        })

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('Email already exists', data['message'])

    def test_weak_password(self):
        """Test registration with weak password"""
        response = self.client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'weak',
            'full_name': 'Test User'
        })

        self.assertEqual(response.status_code, 422)
        data = response.get_json()
        self.assertIn('error', data)

    def test_invalid_email(self):
        """Test registration with invalid email"""
        response = self.client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'invalid-email',
            'password': 'SecurePass123!',
            'full_name': 'Test User'
        })

        self.assertEqual(response.status_code, 422)


class LoginTestCase(AuthServiceTestCase):
    """Login tests"""

    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        with self.app.app_context():
            # Create test user
            self.client.post('/api/auth/register', json={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'SecurePass123!',
                'full_name': 'Test User'
            })

    def test_valid_login(self):
        """Test valid login"""
        response = self.client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'SecurePass123!'
        })

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('access_token', data)
        self.assertIn('refresh_token', data)
        self.assertIn('user', data)

    def test_invalid_password(self):
        """Test login with invalid password"""
        response = self.client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'WrongPassword123!'
        })

        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertIn('Invalid email or password', data['message'])

    def test_nonexistent_user(self):
        """Test login with nonexistent user"""
        response = self.client.post('/api/auth/login', json={
            'email': 'nonexistent@example.com',
            'password': 'SecurePass123!'
        })

        self.assertEqual(response.status_code, 401)


class ProtectedRouteTestCase(AuthServiceTestCase):
    """Protected route tests"""

    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        with self.app.app_context():
            # Create test user
            response = self.client.post('/api/auth/register', json={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'SecurePass123!',
                'full_name': 'Test User'
            })
            
            # Login and get token
            login_response = self.client.post('/api/auth/login', json={
                'email': 'test@example.com',
                'password': 'SecurePass123!'
            })
            
            self.token = login_response.get_json()['access_token']

    def test_get_current_user_with_valid_token(self):
        """Test accessing protected route with valid token"""
        response = self.client.get(
            '/api/auth/me',
            headers={'Authorization': f'Bearer {self.token}'}
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('user', data)
        self.assertEqual(data['user']['email'], 'test@example.com')

    def test_get_current_user_without_token(self):
        """Test accessing protected route without token"""
        response = self.client.get('/api/auth/me')

        self.assertEqual(response.status_code, 401)

    def test_get_current_user_with_invalid_token(self):
        """Test accessing protected route with invalid token"""
        response = self.client.get(
            '/api/auth/me',
            headers={'Authorization': 'Bearer invalid_token'}
        )

        self.assertEqual(response.status_code, 401)


class RBACTestCase(AuthServiceTestCase):
    """RBAC tests"""

    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        with self.app.app_context():
            # Create admin user
            self.client.post('/api/auth/register', json={
                'username': 'admin',
                'email': 'admin@example.com',
                'password': 'SecurePass123!',
                'full_name': 'Admin User'
            })
            
            # Get admin user and assign admin role
            admin_user = User.query.filter_by(email='admin@example.com').first()
            admin_role = Role.query.filter_by(name='admin').first()
            user_role = UserRole.query.filter_by(user_id=admin_user.id).first()
            
            if user_role:
                db.session.delete(user_role)
            
            admin_user_role = UserRole(user_id=admin_user.id, role_id=admin_role.id)
            db.session.add(admin_user_role)
            db.session.commit()
            
            # Login admin and get token
            login_response = self.client.post('/api/auth/login', json={
                'email': 'admin@example.com',
                'password': 'SecurePass123!'
            })
            
            self.admin_token = login_response.get_json()['access_token']

    def test_admin_can_access_admin_endpoint(self):
        """Test admin can access admin-only endpoints"""
        response = self.client.get(
            '/api/admin/users',
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('users', data)

    def test_user_cannot_access_admin_endpoint(self):
        """Test regular user cannot access admin-only endpoints"""
        # Create regular user
        self.client.post('/api/auth/register', json={
            'username': 'regularuser',
            'email': 'user@example.com',
            'password': 'SecurePass123!',
            'full_name': 'Regular User'
        })

        # Login as regular user
        login_response = self.client.post('/api/auth/login', json={
            'email': 'user@example.com',
            'password': 'SecurePass123!'
        })

        user_token = login_response.get_json()['access_token']

        response = self.client.get(
            '/api/admin/users',
            headers={'Authorization': f'Bearer {user_token}'}
        )

        self.assertEqual(response.status_code, 403)


class TokenTestCase(AuthServiceTestCase):
    """JWT token tests"""

    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        with self.app.app_context():
            # Create test user
            self.client.post('/api/auth/register', json={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'SecurePass123!',
                'full_name': 'Test User'
            })
            
            # Login
            login_response = self.client.post('/api/auth/login', json={
                'email': 'test@example.com',
                'password': 'SecurePass123!'
            })
            
            data = login_response.get_json()
            self.access_token = data['access_token']
            self.refresh_token = data['refresh_token']

    def test_refresh_token(self):
        """Test token refresh"""
        response = self.client.post('/api/auth/refresh', json={
            'refresh_token': self.refresh_token
        })

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('access_token', data)
        self.assertEqual(data['token_type'], 'Bearer')


if __name__ == '__main__':
    unittest.main()
