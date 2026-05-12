from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime


class UserRegisterRequest(BaseModel):
    """User registration request schema"""
    username: str = Field(..., min_length=3, max_length=80)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=255)
    full_name: Optional[str] = Field(None, max_length=120)

    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char in '!@#$%^&*' for char in v):
            raise ValueError('Password must contain at least one special character')
        return v

    @validator('username')
    def validate_username(cls, v):
        """Validate username format"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain alphanumeric characters, hyphens, and underscores')
        return v


class UserLoginRequest(BaseModel):
    """User login request schema"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response schema"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
    profile_picture: Optional[str]
    roles: List[str]
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: Optional[str]
    token_type: str = "Bearer"
    expires_in: int
    user: UserResponse


class TokenRefreshRequest(BaseModel):
    """Token refresh request schema"""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Change password request schema"""
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=255)
    confirm_password: str

    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength"""
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char in '!@#$%^&*' for char in v):
            raise ValueError('Password must contain at least one special character')
        return v

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Validate passwords match"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class OAuth2CallbackRequest(BaseModel):
    """OAuth2 callback request schema"""
    code: str
    state: Optional[str]


class GoogleTokenRequest(BaseModel):
    """Google OAuth token request"""
    access_token: str


class GitHubTokenRequest(BaseModel):
    """GitHub OAuth token request"""
    access_token: str


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    message: str
    status_code: int
