"""Tests for server helper utils."""

import pytest

from matter_server.server.helpers.utils import ping_ip


@pytest.mark.asyncio
async def test_ping_ip_rejects_non_positive_attempts() -> None:
    """Negative or zero attempts must fail before the retry loop."""
    with pytest.raises(ValueError, match="positive integer"):
        await ping_ip("127.0.0.1", attempts=0)
    with pytest.raises(ValueError, match="positive integer"):
        await ping_ip("127.0.0.1", attempts=-1)
