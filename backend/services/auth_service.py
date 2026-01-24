"""
Authentication Service
Handles GitHub OAuth flow and JWT token management.
"""
import os
import secrets
import httpx
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class GitHubUser(BaseModel):
    """GitHub user profile data"""
    id: int
    login: str
    name: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    blog: Optional[str] = None
    public_repos: int = 0
    followers: int = 0
    following: int = 0
    html_url: Optional[str] = None


class OAuthTokenResponse(BaseModel):
    """GitHub OAuth token response"""
    access_token: str
    token_type: str = "bearer"
    scope: Optional[str] = None


class AuthUser(BaseModel):
    """Authenticated user data"""
    id: str
    github_id: int
    github_login: str
    avatar_url: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime
    last_login: datetime


class JWTPayload(BaseModel):
    """JWT token payload"""
    sub: str  # user ID
    github_id: int
    github_login: str
    exp: datetime
    iat: datetime


# =============================================================================
# CONFIGURATION
# =============================================================================

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_OAUTH_CALLBACK_URL = os.getenv("GITHUB_OAUTH_CALLBACK_URL", "http://localhost:8000/auth/github/callback")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60480"))  # 7 days


# =============================================================================
# JWT SERVICE
# =============================================================================

class JWTService:
    """Service for JWT token generation and validation"""

    @staticmethod
    def create_access_token(user_id: str, github_id: int, github_login: str) -> str:
        """Create a JWT access token"""
        import jwt

        now = datetime.utcnow()
        payload = {
            "sub": user_id,
            "github_id": github_id,
            "github_login": github_login,
            "iat": now,
            "exp": now + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        }

        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> Optional[JWTPayload]:
        """Decode and validate a JWT token"""
        import jwt

        try:
            payload = jwt.decode(
                token,
                JWT_SECRET_KEY,
                algorithms=[JWT_ALGORITHM]
            )
            return JWTPayload(**payload)
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None


# =============================================================================
# OAUTH SERVICE
# =============================================================================

class AuthService:
    """Service for handling GitHub OAuth flow"""

    def __init__(self):
        self.client_id = GITHUB_CLIENT_ID
        self.client_secret = GITHUB_CLIENT_SECRET
        self.redirect_uri = GITHUB_OAUTH_CALLBACK_URL

    def get_github_auth_url(self, state: Optional[str] = None) -> str:
        """
        Generate GitHub OAuth authorization URL.

        Args:
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL
        """
        if state is None:
            state = secrets.token_urlsafe(16)

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "read:user user:email repo",
            "state": state,
        }

        return f"https://github.com/login/oauth/authorize?{self._format_params(params)}"

    def _format_params(self, params: Dict[str, str]) -> str:
        """Format parameters as URL query string"""
        return "&".join(f"{k}={v}" for k, v in params.items())

    async def exchange_code_for_token(self, code: str, state: str) -> OAuthTokenResponse:
        """
        Exchange OAuth code for access token.

        Args:
            code: Authorization code from GitHub callback
            state: State parameter from callback

        Returns:
            OAuth token response

        Raises:
            httpx.HTTPStatusError: If token exchange fails
        """
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                data=data,
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()
            return OAuthTokenResponse(**response.json())

    async def get_github_user(self, access_token: str) -> GitHubUser:
        """
        Fetch user profile from GitHub using access token.

        Args:
            access_token: GitHub OAuth access token

        Returns:
            GitHub user profile

        Raises:
            httpx.HTTPStatusError: If user fetch fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            response.raise_for_status()
            return GitHubUser(**response.json())

    async def get_user_emails(self, access_token: str) -> list:
        """
        Fetch user emails from GitHub.

        Args:
            access_token: GitHub OAuth access token

        Returns:
            List of email dictionaries
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user/emails",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            response.raise_for_status()
            return response.json()

    def create_user_session(
        self,
        github_user: GitHubUser,
        user_id: Optional[str] = None
    ) -> tuple[str, AuthUser]:
        """
        Create or update user session.

        Args:
            github_user: GitHub user profile
            user_id: Existing user ID (for updates)

        Returns:
            Tuple of (access_token, auth_user)
        """
        # For now, generate a simple user ID
        # In production, this would check/create user in database
        if user_id is None:
            user_id = f"gh_{github_user.id}"

        now = datetime.utcnow()

        auth_user = AuthUser(
            id=user_id,
            github_id=github_user.id,
            github_login=github_user.login,
            avatar_url=github_user.avatar_url,
            name=github_user.name,
            email=github_user.email,
            bio=github_user.bio,
            created_at=now,
            last_login=now
        )

        # Create JWT token
        access_token = JWTService.create_access_token(
            user_id=user_id,
            github_id=github_user.id,
            github_login=github_user.login
        )

        return access_token, auth_user


# Global instances
auth_service = AuthService()
jwt_service = JWTService()


def get_auth_service() -> AuthService:
    """Get the global auth service instance"""
    return auth_service


def get_jwt_service() -> JWTService:
    """Get the global JWT service instance"""
    return jwt_service
