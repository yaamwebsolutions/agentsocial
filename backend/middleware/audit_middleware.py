"""
Audit Middleware - Automatically logs all API requests and responses.

Provides enterprise-grade request logging with:
- Correlation ID tracking for distributed tracing
- Response time monitoring
- Request/response logging
- User context capture
- Error tracking
"""

import time
import uuid
import logging
from typing import Optional, Callable, Awaitable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from middleware.auth_middleware import get_token_payload
from services.audit_service import audit_service
from models import AuditEventType

logger = logging.getLogger(__name__)


# Paths to skip from audit logging (health checks, metrics, etc.)
SKIP_PATHS = {
    "/health",
    "/health/detailed",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
    "/static/",
    # Don't log audit endpoints - prevents infinite loop where reading logs creates more logs
    "/audit",
    "/admin/audit",
}


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically log all API requests for audit trail.

    Features:
    - Generates correlation IDs for request tracing
    - Logs request start and completion
    - Tracks response times
    - Captures user context from auth tokens
    - Logs errors with stack traces
    """

    def __init__(
        self,
        app: ASGIApp,
        skip_paths: Optional[set] = None,
        log_body: bool = False,
        log_response: bool = False,
    ):
        """
        Initialize audit middleware.

        Args:
            app: The ASGI application
            skip_paths: Set of path prefixes to skip logging
            log_body: Whether to log request/response bodies (careful with PII)
            log_response: Whether to log response bodies
        """
        super().__init__(app)
        self.skip_paths = skip_paths or SKIP_PATHS
        self.log_body = log_body
        self.log_response = log_response

    def _should_skip(self, path: str) -> bool:
        """Check if path should be skipped from logging."""
        return any(path.startswith(skip) for skip in self.skip_paths)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request and log to audit trail.

        Args:
            request: The incoming request
            call_next: The next middleware/handler in the chain

        Returns:
            The response from the next handler
        """
        # Skip audit logging for certain paths
        if self._should_skip(request.url.path):
            return await call_next(request)

        # Generate correlation ID for request tracing
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        # Extract user info from request
        user_id = None
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent")

        # Try to get user from authorization header
        try:
            payload = await get_token_payload(
                authorization=request.headers.get("authorization")
            )
            if payload:
                user_id = (
                    payload.get("sub")
                    if isinstance(payload, dict)
                    else (
                        payload.sub
                        if hasattr(payload, "sub")
                        else str(payload)
                        if payload
                        else None
                    )
                )
        except Exception:
            pass  # User not authenticated, that's okay

        # Start timing
        start_time = time.time()

        # Prepare request details for logging
        request_details = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "correlation_id": correlation_id,
            "user_agent": user_agent,
        }

        # Optionally log request body
        if self.log_body and request.method in ("POST", "PUT", "PATCH"):
            try:
                body = await request.body()
                if body:
                    request_details["body"] = body.decode()[:1000]  # Truncate
            except Exception:
                pass

        # Process request (don't log pending - reduces noise, prevents double logging)
        try:
            response = await call_next(request)
        except Exception as e:
            # Log unhandled errors
            response_time_ms = int((time.time() - start_time) * 1000)

            await audit_service.log_event(
                event_type=AuditEventType.SYSTEM_ERROR,
                user_id=user_id,
                resource_type="api_request",
                resource_id=request.url.path,
                details={
                    **request_details,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_ms": response_time_ms,
                },
                status="failed",
                error_message=str(e),
                ip_address=ip_address,
                user_agent=user_agent,
            )

            logger.error(
                f"Request error: {request.method} {request.url.path} - "
                f"{type(e).__name__}: {e}"
            )
            raise

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        # Determine event type based on endpoint
        event_type = self._get_event_type_for_path(
            request.url.path, response.status_code
        )

        # Determine status
        status = "success" if 200 <= response.status_code < 400 else "failed"

        # Update the log with response info
        await audit_service.log_event(
            event_type=event_type,
            user_id=user_id,
            resource_type="api_request",
            resource_id=request.url.path,
            details={
                **request_details,
                "status_code": response.status_code,
                "response_time_ms": response_time_ms,
                "correlation_id": correlation_id,
                "request_id": correlation_id,
            },
            status=status,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Add correlation ID to response headers for tracing
        response.headers["X-Correlation-ID"] = correlation_id

        # Log slow requests
        if response_time_ms > 5000:
            logger.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"took {response_time_ms}ms"
            )

        return response

    def _get_client_ip(self, request: Request) -> Optional[str]:
        """
        Extract client IP address from request.

        Handles proxies and load balancers by checking headers:
        - X-Forwarded-For
        - X-Real-IP
        - CF-Connecting-IP (Cloudflare)
        """
        # Check X-Forwarded-For
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            # X-Forwarded-For can contain multiple IPs, take the first one
            return forwarded.split(",")[0].strip()

        # Check X-Real-IP
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Check Cloudflare
        cf_ip = request.headers.get("cf-connecting-ip")
        if cf_ip:
            return cf_ip

        # Fall back to direct connection
        if request.client:
            return request.client.host

        return None

    def _get_event_type_for_path(self, path: str, status_code: int) -> AuditEventType:
        """
        Map request path to audit event type.

        Args:
            path: The request path
            status_code: The HTTP response status code

        Returns:
            The appropriate audit event type
        """
        # Auth failures (401, 403) are NOT system errors - they're expected
        # Only log actual server errors (500+) as system errors
        if status_code >= 500:
            return AuditEventType.SYSTEM_ERROR
        # Don't log 4xx client errors at all - they're user input issues,
        # not system errors. This prevents 401 auth errors from exploding
        # the audit logs.
        if status_code >= 400:
            return AuditEventType.SYSTEM_STARTUP  # Use generic type, not ERROR

        # Map paths to event types
        if path.startswith("/auth/"):
            if "login" in path:
                return AuditEventType.AUTH_LOGIN
            elif "logout" in path:
                return AuditEventType.AUTH_LOGOUT
            else:
                return AuditEventType.AUTH_LOGIN

        if path.startswith("/posts"):
            if path.endswith("/like"):
                return AuditEventType.POST_LIKE
            elif path.endswith("/unlike"):
                return AuditEventType.POST_UNLIKE
            else:
                return AuditEventType.POST_CREATE

        if path.startswith("/agents"):
            return AuditEventType.AGENT_RUN_COMPLETE

        if path.startswith("/media"):
            if "video" in path:
                return AuditEventType.MEDIA_VIDEO_GENERATE
            else:
                return AuditEventType.MEDIA_IMAGE_GENERATE

        if path.startswith("/search"):
            return AuditEventType.MEDIA_SEARCH

        if path.startswith("/scrape"):
            return AuditEventType.MEDIA_SEARCH

        # Default
        return AuditEventType.SYSTEM_STARTUP


class AuditContextMixin:
    """
    Mixin for request handlers to easily add audit context.

    Usage in endpoints:
        async def my_endpoint(request: Request):
            # Get correlation ID
            correlation_id = request.state.get("correlation_id")

            # Log additional context
            await audit_service.log_event(
                event_type=AuditEventType.COMMAND_EXECUTED,
                user_id=user_id,
                details={"correlation_id": correlation_id, ...}
            )
    """

    @staticmethod
    def get_correlation_id(request: Request) -> str:
        """Get the correlation ID from the request state."""
        return getattr(request.state, "correlation_id", str(uuid.uuid4()))

    @staticmethod
    def get_client_ip(request: Request) -> Optional[str]:
        """Get the client IP address from the request."""
        return getattr(request.state, "client_ip", None)

    @staticmethod
    def get_user_id(request: Request) -> Optional[str]:
        """Get the user ID from the request state."""
        return getattr(request.state, "user_id", None)
