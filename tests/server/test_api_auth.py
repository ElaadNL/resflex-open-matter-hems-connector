"""Tests for optional WebSocket API token auth."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from matter_server.server.helpers.api_auth import (
    authorize_websocket,
    extract_api_token,
    tokens_match,
)


def test_tokens_match() -> None:
    """Matching tokens compare equal; mismatches do not."""
    assert tokens_match("secret", "secret")
    assert not tokens_match("secret", "other")
    assert not tokens_match("short", "longer-token")


def test_extract_api_token_from_bearer_and_query() -> None:
    """Token may come from Authorization or query string."""
    request = MagicMock()
    request.headers = {"Authorization": "Bearer abc123"}
    request.rel_url.query = {}
    assert extract_api_token(request) == "abc123"

    request.headers = {}
    request.rel_url.query = {"token": "from-query"}
    assert extract_api_token(request) == "from-query"


def test_authorize_websocket_disabled_without_token() -> None:
    """Legacy behavior: no configured token means all connections are allowed."""
    server = SimpleNamespace(api_token=None)
    request = MagicMock()
    assert authorize_websocket(server, request) is True


def test_authorize_websocket_requires_matching_token() -> None:
    """Configured token rejects missing/wrong credentials."""
    server = SimpleNamespace(api_token="expected-secret")
    request = MagicMock()
    request.headers = {}
    request.rel_url.query = {}
    request.remote = "127.0.0.1"
    assert authorize_websocket(server, request) is False

    request.headers = {"Authorization": "Bearer expected-secret"}
    assert authorize_websocket(server, request) is True
