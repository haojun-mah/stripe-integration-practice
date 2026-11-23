"""Part 1: integrate the provided HTTP service using Requests."""

import math

import requests


class MapAPIError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class MapClient:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8765",
        api_key: str = "practice-map-key",
        timeout: float = 3.0,
        session: requests.Session | None = None,
    ):
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be a positive finite number")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.session = session if session is not None else requests.Session()
        self._owns_session = session is None

    def render(self, payload: dict) -> bytes:
        """Render a map. Consult docs/STATICMAP_API.md for the wire contract.

        Return successful image bytes, or raise MapAPIError. Do not write files here.
        Use self.session and self.timeout; the session may be injected by a test.
        """
        # TODO: Part 1. Integrate the API; do not call the mock renderer directly.
        raise NotImplementedError("Part 1: implement MapClient.render in bikemap/client.py")

    def close(self):
        if self._owns_session:
            self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
