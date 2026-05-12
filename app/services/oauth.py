import requests
import logging
import secrets
from typing import Optional, Dict, Any, Tuple
from app.models import User, Role, UserRole, db
from app.services.auth import AuthService
from flask import current_app

logger = logging.getLogger(__name__)


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
            username = email.split('@')[0]
            
            # Ensure unique username
            counter = 1
            original_username = username
            while User.query.filter_by(username=username).first():
                username = f"{original_username}{counter}"
                counter += 1

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

            logger.info(f"New Google OAuth user created: {email}")
            return user, None

        except Exception as e:
            db.session.rollback()
            logger.error(f"Google OAuth authentication error: {str(e)}")
            return None, str(e)


class GitHubOAuthService:
    """GitHub OAuth2 service"""

    @staticmethod
    def get_user_info(access_token: str) -> Tuple[Optional[Dict], Optional[str]]:
        """Get user info from GitHub using access token"""
        try:
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

            return response.json(), None

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
            username = login
            
            # Ensure unique username
            counter = 1
            original_username = username
            while User.query.filter_by(username=username).first():
                username = f"{original_username}{counter}"
                counter += 1

            # Use login@ as email if not provided
            if not email:
                email = f"{login}@github.local"

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

            logger.info(f"New GitHub OAuth user created: {login}")
            return user, None

        except Exception as e:
            db.session.rollback()
            logger.error(f"GitHub OAuth authentication error: {str(e)}")
            return None, str(e)
