"""
Auth0 Authentication Service
Handles Auth0 JWT validation and user management.
"""

import json
import httpx
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
from config import (
    AUTH0_DOMAIN,
    AUTH0_CLIENT_ID,
    AUTH0_CLIENT_SECRET,
    AUTH0_AUDIENCE,
    AUTH0_ENABLED,
)


class Auth0Service:
    """Service for Auth0 authentication and token validation."""

    def __init__(self):
        self.domain = AUTH0_DOMAIN
        self.client_id = AUTH0_CLIENT_ID
        self.client_secret = AUTH0_CLIENT_SECRET
        self.audience = AUTH0_AUDIENCE
        self.enabled = AUTH0_ENABLED

        # JWKS cache for token validation
        self._jwks: Optional[Dict[str, Any]] = None
        self._jwks_expires: Optional[datetime] = None

    @property
    def issuer(self) -> str:
        """Get the Auth0 issuer URL."""
        return f"https://{self.domain}"

    @property
    def jwks_url(self) -> str:
        """Get the JWKS URL for token validation."""
        return f"{self.issuer}/.well-known/jwks.json"

    async def get_jwks(self) -> Dict[str, Any]:
        """Get the JSON Web Key Set for token validation."""
        # Cache for 1 hour
        if self._jwks and self._jwks_expires and datetime.now() < self._jwks_expires:
            return self._jwks

        async with httpx.AsyncClient() as client:
            response = await client.get(self.jwks_url)
            response.raise_for_status()
            self._jwks = response.json()
            self._jwks_expires = datetime.now() + timedelta(hours=1)
            return self._jwks

    def get_signing_key(self, jwks: Dict[str, Any], kid: str) -> Optional[str]:
        """Get the signing key from JWKS by key ID."""
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
        return None

    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate an Auth0 JWT access token.

        Args:
            token: The JWT access token from Auth0

        Returns:
            The decoded token payload if valid, None otherwise
        """
        if not self.enabled:
            return None

        try:
            # Get JWKS for validation
            jwks = await self.get_jwks()

            # Decode header to get key ID
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")

            if not kid:
                return None

            # Get signing key
            signing_key = self.get_signing_key(jwks, kid)
            if not signing_key:
                return None

            # Use audience for validation only if it's a valid, non-placeholder value
            # This matches the logic in get_login_url
            valid_audience = None
            if (
                self.audience
                and self.audience.strip()
                and self.audience not in ("****", "YOUR_API_AUDIENCE")
            ):
                valid_audience = self.audience

            # Validate token - if no valid audience, use client_id as default
            payload = jwt.decode(
                token,
                key=signing_key,
                algorithms=["RS256"],
                audience=valid_audience or self.client_id,
                issuer=self.issuer,
                options={"verify_aud": bool(valid_audience), "verify_iss": True},
            )

            return payload

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError as e:
            # Log for debugging but don't expose errors
            import logging

            logging.getLogger(__name__).warning(f"Auth0 token validation failed: {e}")
            return None
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(f"Auth0 token validation error: {e}")
            return None

    async def get_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile from Auth0 using access token.

        Args:
            token: Valid Auth0 access token

        Returns:
            User profile data or None
        """
        if not self.enabled:
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.issuer}/userinfo",
                    headers={"Authorization": f"Bearer {token}"},
                )
                response.raise_for_status()
                return response.json()
        except Exception:
            return None

    async def exchange_code_for_token(
        self, code: str, redirect_uri: str
    ) -> Optional[Dict[str, Any]]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from Auth0 callback
            redirect_uri: The redirect URI used in the initial request

        Returns:
            Token response with access_token, id_token, etc. or None
        """
        import logging

        logger = logging.getLogger(__name__)

        if not self.enabled:
            logger.error("Auth0 not enabled but exchange_code_for_token was called")
            return None

        if not self.client_secret or self.client_secret in ("****", "YOUR_CLIENT_SECRET"):
            logger.error("AUTH0_CLIENT_SECRET is not configured properly")
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.issuer}/oauth/token",
                    data={
                        "grant_type": "authorization_code",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "code": code,
                        "redirect_uri": redirect_uri,
                    },
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Auth0 token exchange HTTP error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Auth0 token exchange error: {type(e).__name__}: {e}")
            return None

    def get_login_url(
        self,
        redirect_uri: str,
        state: Optional[str] = None,
        connection: Optional[str] = None,
        scope: str = "openid profile email",
    ) -> str:
        """
        Get the Auth0 universal login URL.

        Args:
            redirect_uri: Where to redirect after login
            state: CSRF protection parameter
            connection: Specific Auth0 connection (e.g., "github", "google")
            scope: OAuth scopes

        Returns:
            Full Auth0 login URL
        """
        from urllib.parse import urlencode

        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope,
        }

        if state:
            params["state"] = state
        if connection:
            params["connection"] = connection
        # Only include audience if it's a valid, non-empty, non-placeholder value
        # This avoids the "Service not found" error when audience is misconfigured
        if (
            self.audience
            and self.audience.strip()
            and self.audience not in ("****", "YOUR_API_AUDIENCE")
        ):
            params["audience"] = self.audience

        return f"{self.issuer}/authorize?{urlencode(params)}"

    def get_logout_url(self, return_to: str, client_id: Optional[str] = None) -> str:
        """
        Get the Auth0 logout URL.

        Args:
            return_to: Where to redirect after logout
            client_id: Optional client ID for federated logout

        Returns:
            Full Auth0 logout URL
        """
        params = {"returnTo": return_to}
        if client_id or self.client_id:
            params["client_id"] = client_id or self.client_id

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.issuer}/v2/logout?{query_string}"

    def normalize_user(self, auth0_user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Auth0 user data to a standard format.

        Args:
            auth0_user: Raw user data from Auth0

        Returns:
            Normalized user object
        """
        return {
            "sub": auth0_user.get("sub"),
            "user_id": auth0_user.get("user_id") or auth0_user.get("sub"),
            "email": auth0_user.get("email"),
            "email_verified": auth0_user.get("email_verified", False),
            "name": auth0_user.get("name"),
            "nickname": auth0_user.get("nickname"),
            "picture": auth0_user.get("picture"),
            "updated_at": auth0_user.get("updated_at"),
            "auth0_id": auth0_user.get("sub"),
            # Handle social provider data
            "github_login": auth0_user.get("nickname", ""),
            "avatar_url": auth0_user.get("picture"),
        }


# Singleton instance
_auth0_service: Optional[Auth0Service] = None


def get_auth0_service() -> Auth0Service:
    """Get the singleton Auth0Service instance."""
    global _auth0_service
    if _auth0_service is None:
        _auth0_service = Auth0Service()
    return _auth0_service
