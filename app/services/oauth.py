import requests
import logging
import secrets
import re
from typing import Optional, Dict, Any, Tuple
from app.models import User, Role, UserRole, db
from app.services.auth import AuthService
from flask import current_app

logger = logging.getLogger(__name__)


def _sanitize_username(username: str) -> str:
    """
    Sanitize username for database constraints.
    - Convert to lowercase
    - Replace non-alphanumeric (except underscores) with underscores
    - Strip leading/trailing underscores
    - Collapse multiple underscores
    """
    # Convert to lowercase
    username = username.lower()
    
    # Replace non-alphanumeric with underscores
    username = re.sub(r'[^a-z0-9_]', '_', username)
    
    # Collapse multiple underscores
    username = re.sub(r'_+', '_', username)
    
    # Strip leading/trailing underscores
    username = username.strip('_')
    
    # Fallback if empty after stripping
    if not username:
        username = f"user_{secrets.token_hex(4)}"
        
    return username


class GoogleOAuthService:
    """Google OAuth2 service"""

    @staticmethod
    def get_user_info(access_token: str) -> Tuple[Optional[Dict], Optional[str]]:
        """Get user info from Google using access token"""
        try:
            response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=5
            )

            if response.status_code != 200:
                return None, "Failed to get user info from Google"

            return response.json(), None

        except requests.RequestException as e:
            logger.error(f"Google API request error: {str(e)}")
            return None, "Failed to connect to Google"
        except Exception as e:
            logger.error(f"Google OAuth error: {str(e)}")
            return None, str(e)

    @staticmethod
    def authenticate_or_create_user(user_info: Dict) -> Tuple[Optional[User], Optional[str]]:
        """Authenticate or create user from Google info"""
        try:
            google_id = user_info.get('id')
            email = user_info.get('email')
            name = user_info.get('name')
            picture = user_info.get('picture')

            if not google_id or not email:
                return None, "Invalid Google user info"

            # Try to find existing user by OAuth ID
            user = User.query.filter_by(oauth_id=google_id, oauth_provider='google').first()

            if user:
                logger.info(f"Google OAuth user found: {user.email}")
                return user, None

            # Try to find existing user by email
            user = User.query.filter_by(email=email).first()

            if user:
                # Link Google account
                user.oauth_id = google_id
                user.oauth_provider = 'google'
                if not user.profile_picture and picture:
                    user.profile_picture = picture
                db.session.commit()
                logger.info(f"Google OAuth linked to existing user: {email}")
                return user, None

            # Create new user
            username = _sanitize_username(email.split('@')[0])
            
            # Ensure unique username
            counter = 1
            original_username = username
            while User.query.filter_by(username=username).first():
                username = f"{original_username}{counter}"
                counter += 1

            logger.info(f"Creating new Google OAuth user: provider=google, email={email}, username={username}")

            user = User(
                username=username,
                email=email,
                password_hash=AuthService.hash_password(secrets.token_hex(32)),
                full_name=name,
                oauth_id=google_id,
                oauth_provider='google',
                profile_picture=picture,
                is_verified=True  # OAuth users are verified
            )

            # Add default USER role
            user_role = UserRole(user=user, role=Role.query.filter_by(name='user').first())

            db.session.add(user)
            db.session.add(user_role)
            db.session.commit()

            logger.info(f"New Google OAuth user created successfully: {email}")
            return user, None

        except Exception as e:
            db.session.rollback()
            logger.error(f"Google OAuth authentication error for {user_info.get('email')}: {str(e)}")
            return None, str(e)


class GitHubOAuthService:
    """GitHub OAuth2 service (Authorization Code Flow)"""

    @staticmethod
    def exchange_code_for_token(code: str) -> Tuple[Optional[str], Optional[str]]:
        """Exchange authorization code for access token"""
        try:
            client_id = current_app.config.get('GITHUB_CLIENT_ID')
            client_secret = current_app.config.get('GITHUB_CLIENT_SECRET')

            if not client_id or not client_secret:
                return None, "GitHub OAuth configuration is missing"

            response = requests.post(
                'https://github.com/login/oauth/access_token',
                headers={'Accept': 'application/json'},
                data={
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'code': code
                },
                timeout=10
            )

            if response.status_code != 200:
                return None, f"GitHub token exchange failed: {response.text}"

            data = response.json()
            access_token = data.get('access_token')

            if not access_token:
                return None, f"GitHub returned no access token: {data.get('error_description', 'Unknown error')}"

            return access_token, None

        except requests.RequestException as e:
            logger.error(f"GitHub token exchange request error: {str(e)}")
            return None, "Failed to connect to GitHub for token exchange"
        except Exception as e:
            logger.error(f"GitHub token exchange error: {str(e)}")
            return None, str(e)

    @staticmethod
    def get_user_info(access_token: str) -> Tuple[Optional[Dict], Optional[str]]:
        """Get user info and email from GitHub using access token"""
        try:
            # 1. Get base profile
            response = requests.get(
                'https://api.github.com/user',
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Accept': 'application/vnd.github.v3+json'
                },
                timeout=5
            )

            if response.status_code != 200:
                return None, "Failed to get user info from GitHub"

            user_info = response.json()

            # 2. Get email if not public in profile
            if not user_info.get('email'):
                email_res = requests.get(
                    'https://api.github.com/user/emails',
                    headers={
                        'Authorization': f'Bearer {access_token}',
                        'Accept': 'application/vnd.github.v3+json'
                    },
                    timeout=5
                )
                if email_res.status_code == 200:
                    emails = email_res.json()
                    # Find primary, verified email
                    primary_email = next((e['email'] for e in emails if e['primary'] and e['verified']), None)
                    if not primary_email and emails:
                        primary_email = emails[0]['email']
                    user_info['email'] = primary_email

            return user_info, None

        except requests.RequestException as e:
            logger.error(f"GitHub API request error: {str(e)}")
            return None, "Failed to connect to GitHub"
        except Exception as e:
            logger.error(f"GitHub OAuth error: {str(e)}")
            return None, str(e)

    @staticmethod
    def authenticate_or_create_user(user_info: Dict) -> Tuple[Optional[User], Optional[str]]:
        """Authenticate or create user from GitHub info"""
        try:
            github_id = user_info.get('id')
            email = user_info.get('email')
            login = user_info.get('login')
            name = user_info.get('name')
            avatar_url = user_info.get('avatar_url')

            if not github_id or not login:
                return None, "Invalid GitHub user info"

            # Try to find existing user by OAuth ID
            user = User.query.filter_by(oauth_id=str(github_id), oauth_provider='github').first()

            if user:
                logger.info(f"GitHub OAuth user found: {user.email}")
                return user, None

            # Try to find existing user by email (if available)
            if email:
                user = User.query.filter_by(email=email).first()
                if user:
                    user.oauth_id = str(github_id)
                    user.oauth_provider = 'github'
                    if not user.profile_picture and avatar_url:
                        user.profile_picture = avatar_url
                    db.session.commit()
                    logger.info(f"GitHub OAuth linked to existing user: {email}")
                    return user, None

            # Create new user
            username = _sanitize_username(login)
            
            # Ensure unique username
            counter = 1
            original_username = username
            while User.query.filter_by(username=username).first():
                username = f"{original_username}{counter}"
                counter += 1

            # Use login@ as email if not provided
            if not email:
                email = f"{login}@github.local"

            logger.info(f"Creating new GitHub OAuth user: provider=github, email={email}, username={username}")

            user = User(
                username=username,
                email=email,
                password_hash=AuthService.hash_password(secrets.token_hex(32)),
                full_name=name or login,
                oauth_id=str(github_id),
                oauth_provider='github',
                profile_picture=avatar_url,
                is_verified=True  # OAuth users are verified
            )

            # Add default USER role
            user_role = UserRole(user=user, role=Role.query.filter_by(name='user').first())

            db.session.add(user)
            db.session.add(user_role)
            db.session.commit()

            logger.info(f"New GitHub OAuth user created successfully: {login}")
            return user, None

        except Exception as e:
            db.session.rollback()
            logger.error(f"GitHub OAuth authentication error for {user_info.get('email', login)}: {str(e)}")
            return None, str(e)
