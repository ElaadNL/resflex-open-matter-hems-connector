"""Shared pytest fixtures and third-party compatibility shims.

aiohttp 3.14 made ``stream_writer`` a required keyword-only argument of
``ClientResponse.__init__``. Released ``aioresponses`` (including 0.7.8)
does not pass it, so mocked requests raise ``TypeError`` under aiohttp >= 3.14.

Until an upstream aioresponses release includes the fix
(https://github.com/pnuckowski/aioresponses/pull/288 /
https://github.com/pnuckowski/aioresponses/issues/289), swap the response
class aioresponses instantiates for one that supplies the missing argument.

``ClientResponse`` only reads ``stream_writer.output_size`` when ``writer`` is
``None`` (how aioresponses builds responses), so a lightweight mock is enough.
The signature check keeps this a no-op on aiohttp < 3.14 and once aioresponses
passes ``stream_writer`` itself.
"""

from __future__ import annotations

import inspect
from typing import Any
from unittest.mock import Mock

from aiohttp import ClientResponse
import aioresponses.core as _aioresponses_core

# Test-only compat shim for aiohttp 3.14 + aioresponses
if "stream_writer" in inspect.signature(ClientResponse.__init__).parameters:

    class _CompatClientResponse(ClientResponse):
        """ClientResponse that defaults the aiohttp 3.14 stream_writer."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            kwargs.setdefault("stream_writer", Mock(output_size=0))
            super().__init__(*args, **kwargs)

    # aioresponses instantiates whatever core.ClientResponse points at.
    _aioresponses_core.ClientResponse = _CompatClientResponse  # type: ignore[attr-defined]
