"""
Admin Access Control - Enforces admin-only access for sensitive endpoints.

Provides dependency functions for FastAPI to protect admin routes.
"""

import os
from typing import Optional, Dict, Any, List

from fastapi import HTTPException, Depends
from starlette.status import HTTP_403_FORBIDDEN, HTTP_401_UNAUTHORIZED

from middleware.auth_middleware import get_token_payload, UserPayload
from config import AUTH0_ENABLED, ADMIN_USER_IDS, ADMIN_EMAIL_DOMAINS

# =============================================================================
# ADMIN CONFIGURATION
# =============================================================================

# Parse admin user IDs from environment (comma-separated)
_ADMIN_USER_ID_LIST: List[str] = [
    uid.strip() for uid in ADMIN_USER_IDS.split(",") if uid.strip()
]

# Parse admin email domains from environment (comma-separated)
_ADMIN_DOMAIN_LIST: List[str] = [
    domain.strip() for domain in ADMIN_EMAIL_DOMAINS.split(",") if domain.strip()
]


def is_admin_user(payload: UserPayload) -> bool:
    """
    Check if a user payload has admin privileges.

    Args:
        payload: User payload from auth token

    Returns:
        True if user is admin, False otherwise
    """
    if not payload:
        return False

    user_id = None
    email = None

    # Extract user_id and email from different payload types
    if isinstance(payload, dict):
        user_id = payload.get("sub")
        email = payload.get("email")
    elif hasattr(payload, "sub"):
        user_id = payload.sub
        email = getattr(payload, "email", None)

    # Check admin user IDs
    if user_id and user_id in _ADMIN_USER_ID_LIST:
        return True

    # Check admin email domains
    if email and _ADMIN_DOMAIN_LIST:
        email_domain = email.split("@")[-1].lower()
        if email_domain in _ADMIN_DOMAIN_LIST:
            return True

    return False


async def require_admin(
    payload: Optional[UserPayload] = Depends(get_token_payload),
) -> UserPayload:
    """
    Dependency that requires admin privileges.

    Raises HTTP 401 if not authenticated.
    Raises HTTP 403 if authenticated but not admin.

    Usage:
        @app.get("/admin/users")
        async def list_users(_admin: UserPayload = Depends(require_admin)):
            return {"users": [...]}

    Args:
        payload: User payload from auth token

    Returns:
        The user payload if admin

    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin
    """
    if not payload:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not is_admin_user(payload):
        # Get user info for error message
        user_id = (
            payload.get("sub")
            if isinstance(payload, dict)
            else payload.sub
            if hasattr(payload, "sub")
            else "unknown"
        )

        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail=f"User {user_id} does not have admin privileges",
        )

    return payload


async def get_optional_admin(
    payload: Optional[UserPayload] = Depends(get_token_payload),
) -> Optional[UserPayload]:
    """
    Dependency that returns user payload only if they are an admin.

    Unlike require_admin, this does not raise an error if the user
    is not an admin - it just returns None.

    Usage:
        @app.get("/public-endpoint")
        async def public_endpoint(
            _admin: Optional[UserPayload] = Depends(get_optional_admin)
        ):
            if _admin:
                # Show admin features
                pass
            else:
                # Show regular user features
                pass

    Args:
        payload: User payload from auth token

    Returns:
        The user payload if admin, None otherwise
    """
    if payload and is_admin_user(payload):
        return payload
    return None


async def require_admin_or_role(required_roles: List[str] = None):
    """
    Dependency that requires admin OR specific roles.

    This allows for role-based access control beyond just admin.

    Args:
        required_roles: List of acceptable roles

    Usage:
        @app.get("/admin/users")
        async def list_users(
            _user: UserPayload = Depends(require_admin_or_role(["moderator", "admin"]))
        ):
            return {"users": [...]}
    """

    async def check_role(
        payload: Optional[UserPayload] = Depends(get_token_payload),
    ) -> UserPayload:
        if not payload:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if admin first
        if is_admin_user(payload):
            return payload

        # Check for required roles
        if required_roles:
            user_role = None
            if isinstance(payload, dict):
                user_role = payload.get("role")
                # Also check Auth0 app_metadata or namespace
                if not user_role:
                    user_role = payload.get("app_metadata", {}).get(
                        "role"
                    ) or payload.get(f"{os.getenv('AUTH0_AUDIENCE', '')}/role")
            elif hasattr(payload, "role"):
                user_role = payload.role

            if user_role in required_roles:
                return payload

        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail=f"Admin or role {required_roles} required",
        )

    return check_role


def get_admin_config() -> Dict[str, Any]:
    """
    Get current admin configuration for debugging.

    Returns a sanitized version without sensitive data.
    """
    return {
        "admin_user_ids_count": len(_ADMIN_USER_ID_LIST),
        "admin_email_domains": _ADMIN_DOMAIN_LIST,
        "auth0_enabled": AUTH0_ENABLED,
    }


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def add_admin_user(user_id: str) -> bool:
    """Add a user ID to the admin list at runtime."""
    if user_id not in _ADMIN_USER_ID_LIST:
        _ADMIN_USER_ID_LIST.append(user_id)
        return True
    return False


def remove_admin_user(user_id: str) -> bool:
    """Remove a user ID from the admin list at runtime."""
    if user_id in _ADMIN_USER_ID_LIST:
        _ADMIN_USER_ID_LIST.remove(user_id)
        return True
    return False


def add_admin_domain(domain: str) -> bool:
    """Add an email domain to the admin list at runtime."""
    domain = domain.lower()
    if domain not in _ADMIN_DOMAIN_LIST:
        _ADMIN_DOMAIN_LIST.append(domain)
        return True
    return False


def remove_admin_domain(domain: str) -> bool:
    """Remove an email domain from the admin list at runtime."""
    domain = domain.lower()
    if domain in _ADMIN_DOMAIN_LIST:
        _ADMIN_DOMAIN_LIST.remove(domain)
        return True
    return False
