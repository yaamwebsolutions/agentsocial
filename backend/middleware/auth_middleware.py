"""
Authentication Middleware
FastAPI dependencies for protected routes.
Supports both Auth0 tokens and internal JWT tokens.
"""

from typing import Optional, Union, Dict, Any
from datetime import datetime, timedelta
from fastapi import Header, HTTPException, Depends
from services.auth_service import JWTPayload, get_jwt_service
from services.auth0_service import get_auth0_service
from config import AUTH0_ENABLED
import logging
import asyncio

logger = logging.getLogger(__name__)

__all__ = ["get_current_user", "get_optional_user", "get_token_payload"]


# Type alias for user payload
UserPayload = Union[JWTPayload, Dict[str, Any]]


# Simple in-memory cache for validated tokens to reduce Auth0 API calls
# Cache key: token hash, value: (payload, expiry time)
_token_cache: Dict[str, tuple[Dict[str, Any], datetime]] = {}
_cache_lock = asyncio.Lock()


def _hash_token(token: str) -> str:
    """Simple hash for token caching (not cryptographically secure, just for deduplication)"""
    import hashlib

    return hashlib.sha256(token.encode()).hexdigest()[:32]


async def _get_cached_token(token_hash: str) -> Optional[Dict[str, Any]]:
    """Get cached token payload if still valid"""
    async with _cache_lock:
        if token_hash in _token_cache:
            payload, expiry = _token_cache[token_hash]
            if datetime.now() < expiry:
                return payload
            else:
                del _token_cache[token_hash]
    return None


async def _cache_token(token_hash: str, payload: Dict[str, Any], ttl_minutes: int = 5):
    """Cache validated token payload"""
    async with _cache_lock:
        _token_cache[token_hash] = (
            payload,
            datetime.now() + timedelta(minutes=ttl_minutes),
        )


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
    token_hash = _hash_token(token)

    # Check cache first
    cached = await _get_cached_token(token_hash)
    if cached:
        return cached

    # Try Auth0 validation first if enabled
    if AUTH0_ENABLED:
        auth0_service = get_auth0_service()

        # First try to validate as JWT (for id_token)
        jwt_payload = await auth0_service.validate_token(token)
        if jwt_payload:
            await _cache_token(token_hash, jwt_payload, ttl_minutes=5)
            return jwt_payload

        # If JWT validation fails, try validating as opaque access_token via userinfo
        # This handles Auth0 access_tokens which are opaque tokens
        # Only do this if not recently rate-limited (check last call result)
        user_info = await auth0_service.get_user_info(token)
        if user_info:
            await _cache_token(
                token_hash, user_info, ttl_minutes=2
            )  # Cache for shorter time
            return user_info

    # Fall back to internal JWT validation (for GitHub login tokens)
    jwt_service = get_jwt_service()
    internal_payload = jwt_service.decode_token(token)
    if internal_payload:
        # Cache internal tokens too
        await _cache_token(token_hash, internal_payload.dict(), ttl_minutes=5)
        return internal_payload

    return None


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
