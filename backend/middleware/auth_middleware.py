"""
Authentication Middleware
FastAPI dependencies for protected routes.
Supports both Auth0 tokens and internal JWT tokens.
"""

from typing import Optional, Union, Dict, Any
from datetime import datetime
from fastapi import Header, HTTPException, Depends
from services.auth_service import JWTService, JWTPayload, get_jwt_service
from services.auth0_service import get_auth0_service
from config import AUTH0_ENABLED

__all__ = ["get_current_user", "get_optional_user", "get_token_payload"]


# Type alias for user payload
UserPayload = Union[JWTPayload, Dict[str, Any]]


async def get_token_payload(
    authorization: Optional[str] = Header(None),
) -> Optional[UserPayload]:
    """
    Extract and validate token from Authorization header.
    Supports both Auth0 tokens (access_token and id_token) and internal JWT tokens.

    Args:
        authorization: Authorization header value

    Returns:
        User payload if token is valid, None otherwise
    """
    if not authorization:
        return None

    if not authorization.startswith("Bearer "):
        return None

    token = authorization.split(" ")[1]

    # Try Auth0 validation first if enabled
    if AUTH0_ENABLED:
        auth0_service = get_auth0_service()

        # First try to validate as JWT (for id_token)
        payload = await auth0_service.validate_token(token)
        if payload:
            return payload

        # If JWT validation fails, try validating as opaque access_token via userinfo
        # This handles Auth0 access_tokens which are opaque tokens
        user_info = await auth0_service.get_user_info(token)
        if user_info:
            return user_info

    # Fall back to internal JWT validation
    jwt_service = get_jwt_service()
    return jwt_service.decode_token(token)


async def get_current_user(
    payload: Optional[UserPayload] = Depends(get_token_payload),
) -> UserPayload:
    """
    Get authenticated user. Raises 401 if not authenticated.

    Args:
        payload: Token payload from Auth0 or internal JWT

    Returns:
        User payload

    Raises:
        HTTPException: 401 if not authenticated
    """
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check expiration for internal JWT
    if isinstance(payload, JWTPayload) and hasattr(payload, "exp"):
        if payload.exp < datetime.now():
            raise HTTPException(
                status_code=401,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Check expiration for Auth0 JWT
    if isinstance(payload, dict):
        exp = payload.get("exp")
        if exp and exp < datetime.now().timestamp():
            raise HTTPException(
                status_code=401,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return payload


async def get_optional_user(
    payload: Optional[UserPayload] = Depends(get_token_payload),
) -> Optional[UserPayload]:
    """
    Get authenticated user if present, but don't raise error if not.

    Args:
        payload: Token payload from Auth0 or internal JWT

    Returns:
        User payload if authenticated, None otherwise
    """
    return payload
