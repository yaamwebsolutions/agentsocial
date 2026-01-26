"""
OAuth state utilities for CSRF protection.
Uses a signed, time-limited token to avoid server-side storage.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from typing import Optional

from config import OAUTH_STATE_SECRET, OAUTH_STATE_TTL_SECONDS


def _sign(payload: str) -> str:
    digest = hmac.new(
        OAUTH_STATE_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


def generate_oauth_state() -> str:
    """Generate a signed OAuth state token."""
    nonce = secrets.token_urlsafe(16)
    timestamp = str(int(time.time()))
    payload = f"{nonce}.{timestamp}"
    signature = _sign(payload)
    return f"{payload}.{signature}"


def verify_oauth_state(state: Optional[str]) -> bool:
    """Validate a signed OAuth state token with TTL."""
    if not state:
        return False

    parts = state.split(".")
    if len(parts) != 3:
        return False

    nonce, timestamp, signature = parts
    if not nonce or not timestamp or not signature:
        return False

    payload = f"{nonce}.{timestamp}"
    expected = _sign(payload)
    if not hmac.compare_digest(signature, expected):
        return False

    try:
        issued_at = int(timestamp)
    except ValueError:
        return False

    now = int(time.time())
    if issued_at > now + 60:
        return False

    return now - issued_at <= OAUTH_STATE_TTL_SECONDS
