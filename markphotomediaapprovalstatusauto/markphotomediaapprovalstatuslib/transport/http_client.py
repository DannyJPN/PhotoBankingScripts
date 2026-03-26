"""HTTP transport layer using httpx with rate limiting and retries."""

import logging
import time
from types import TracebackType
from typing import Optional, Type

import httpx

_DEFAULT_HEADERS = {
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class HttpClient:
    """Thin httpx wrapper with rate limiting, retry, and locale headers.

    :param timeout: Request timeout in seconds.
    :param retries: Number of retry attempts on transient errors.
    :param rate_limit_delay: Minimum seconds between consecutive requests.
    """

    def __init__(
        self,
        timeout: int = 30,
        retries: int = 3,
        rate_limit_delay: float = 1.0,
    ) -> None:
        self._client = httpx.Client(
            headers=_DEFAULT_HEADERS,
            timeout=timeout,
            follow_redirects=True,
        )
        self._retries = retries
        self._rate_limit_delay = rate_limit_delay
        self._last_request_time: float = 0.0

    def get(self, url: str, **kwargs) -> httpx.Response:
        """Perform a GET request with rate limiting and retries.

        :param url: Target URL.
        :return: httpx Response object.
        :raises httpx.HTTPStatusError: On non-retriable HTTP errors.
        :raises httpx.RequestError: On connection errors after all retries.
        """
        self._throttle()
        last_exc: Optional[Exception] = None
        for attempt in range(self._retries):
            try:
                response = self._client.get(url, **kwargs)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429:
                    wait = 2**attempt
                    logging.warning("Rate limited by %s, waiting %ss", url, wait)
                    time.sleep(wait)
                    last_exc = exc
                    continue
                raise
            except httpx.RequestError as exc:
                logging.warning("Request error attempt %d/%d for %s: %s", attempt + 1, self._retries, url, exc)
                last_exc = exc
                if attempt < self._retries - 1:
                    time.sleep(1)
        raise last_exc  # type: ignore[misc]

    def head(self, url: str, **kwargs) -> httpx.Response:
        """Perform a HEAD request.

        :param url: Target URL.
        :return: httpx Response object.
        """
        self._throttle()
        return self._client.head(url, **kwargs)

    def _throttle(self) -> None:
        """Enforce minimum delay between requests."""
        now = time.monotonic()
        elapsed = now - self._last_request_time
        if elapsed < self._rate_limit_delay:
            time.sleep(self._rate_limit_delay - elapsed)
        self._last_request_time = time.monotonic()

    def close(self) -> None:
        """Close the underlying httpx client."""
        self._client.close()

    def __enter__(self) -> "HttpClient":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.close()
