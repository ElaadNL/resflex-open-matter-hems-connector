"""Optional shared-secret auth for the WebSocket control API."""

from __future__ import annotations

import hmac
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiohttp import web

    from matter_server.server.server import MatterServer

LOGGER = logging.getLogger(__name__)


def extract_api_token(request: web.Request) -> str | None:
    """Extract a bearer/query token from an incoming WebSocket request."""
    auth = request.headers.get("Authorization")
    if auth:
        scheme, _, value = auth.partition(" ")
        if scheme.lower() == "bearer" and value:
            return value.strip()
    return request.rel_url.query.get("token") or request.rel_url.query.get(
        "access_token"
    )


def tokens_match(provided: str, expected: str) -> bool:
    """Constant-time token comparison."""
    provided_bytes = provided.encode("utf-8")
    expected_bytes = expected.encode("utf-8")
    if len(provided_bytes) != len(expected_bytes):
        return False
    return hmac.compare_digest(provided_bytes, expected_bytes)


def authorize_websocket(server: MatterServer, request: web.Request) -> bool:
    """Return True when the request is allowed to open the control WebSocket.

    If ``server.api_token`` is unset, authentication is disabled (legacy behavior).
    """
    expected = server.api_token
    if not expected:
        return True
    provided = extract_api_token(request)
    if not provided or not tokens_match(provided, expected):
        LOGGER.warning(
            "Rejected unauthenticated WebSocket connection from %s",
            request.remote,
        )
        return False
    return True
