"""
Authentication Middleware
FastAPI dependencies for protected routes.
"""
from typing import Optional
from datetime import datetime
from fastapi import Header, HTTPException, Depends
from services.auth_service import JWTService, JWTPayload, get_jwt_service

__all__ = ["get_current_user", "get_optional_user", "get_token_payload"]


async def get_token_payload(
    authorization: Optional[str] = Header(None)
) -> Optional[JWTPayload]:
    """
    Extract and validate JWT token from Authorization header.

    Args:
        authorization: Authorization header value

    Returns:
        JWTPayload if token is valid, None otherwise
    """
    if not authorization:
        return None

    if not authorization.startswith("Bearer "):
        return None

    token = authorization.split(" ")[1]
    jwt_service = get_jwt_service()
    return jwt_service.decode_token(token)


async def get_current_user(
    payload: Optional[JWTPayload] = Depends(get_token_payload)
) -> JWTPayload:
    """
    Get authenticated user. Raises 401 if not authenticated.

    Args:
        payload: JWT payload from token

    Returns:
        JWTPayload

    Raises:
        HTTPException: 401 if not authenticated
    """
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if token is expired
    if payload.exp < datetime.now():
        raise HTTPException(
            status_code=401,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def get_optional_user(
    payload: Optional[JWTPayload] = Depends(get_token_payload)
) -> Optional[JWTPayload]:
    """
    Get authenticated user if present, but don't raise error if not.

    Args:
        payload: JWT payload from token

    Returns:
        JWTPayload if authenticated, None otherwise
    """
    return payload
