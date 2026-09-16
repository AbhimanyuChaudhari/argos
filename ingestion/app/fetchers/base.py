import httpx
import asyncio
from abc import ABC, abstractmethod
from typing import Any, Optional
from loguru import logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.core.config import settings


class BaseFetcher(ABC):
    """
    Base class for all Argos data fetchers.
    Handles retry logic, rate limiting,
    error handling, and logging automatically.
    Every fetcher inherits from this class
    and implements fetch() and normalise().
    """

    # Override in subclass
    SOURCE_NAME: str = "unknown"
    BASE_URL: str = ""

    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        self.timeout = settings.REQUEST_TIMEOUT
        self.max_retries = settings.MAX_RETRIES

    async def __aenter__(self):
        """
        Creates the HTTP client when entering
        an async context manager.
        Usage:
            async with MyFetcher() as fetcher:
                data = await fetcher.fetch()
        """
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers=self._get_headers(),
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, *args):
        """
        Closes the HTTP client on exit.
        Always called even if an exception occurs.
        """
        if self.client:
            await self.client.aclose()

    def _get_headers(self) -> dict:
        """
        Default headers for all requests.
        Override in subclass to add auth headers.
        SEC EDGAR requires a User-Agent header
        with contact info — it will block requests
        without it.
        """
        return {
            "User-Agent": "Argos Financial Terminal contact@argos.finance",
            "Accept": "application/json",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (httpx.TimeoutException, httpx.ConnectError)
        ),
    )
    async def _get(
        self,
        url: str,
        params: Optional[dict] = None,
    ) -> dict:
        """
        Makes a GET request with automatic retry.
        Retries up to 3 times on timeout or
        connection errors with exponential backoff.
        2s → 4s → 8s between retries.
        """
        if not self.client:
            raise RuntimeError(
                "Client not initialised. "
                "Use async with fetcher as f: syntax."
            )

        logger.debug(f"GET {url} params={params}")

        response = await self.client.get(url, params=params)

        if response.status_code == 429:
            # Rate limited — wait and retry
            retry_after = int(
                response.headers.get("Retry-After", 60)
            )
            logger.warning(
                f"Rate limited by {self.SOURCE_NAME}. "
                f"Waiting {retry_after}s"
            )
            await asyncio.sleep(retry_after)
            response = await self.client.get(url, params=params)

        response.raise_for_status()
        return response.json()

    async def _get_with_fallback(
        self,
        url: str,
        params: Optional[dict] = None,
        fallback: Any = None,
    ) -> Any:
        """
        GET request that returns a fallback value
        instead of raising on error.
        Use when a missing record is acceptable.
        """
        try:
            return await self._get(url, params)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.debug(f"404 at {url} — returning fallback")
                return fallback
            raise

    @abstractmethod
    async def fetch(self, **kwargs) -> list[dict]:
        """
        Fetches raw data from the source API.
        Must be implemented by every fetcher.
        Returns a list of raw API response dicts.
        """
        pass

    @abstractmethod
    def normalise(self, raw: dict) -> Optional[dict]:
        """
        Converts a raw API response dict into
        a normalised dict matching the database model.
        Must be implemented by every fetcher.
        Returns None if the record should be skipped.
        """
        pass

    async def run(self, **kwargs) -> list[dict]:
        """
        Full pipeline: fetch → normalise → return.
        Called by the scheduler.
        Logs success and failure counts.
        """
        logger.info(f"Starting {self.SOURCE_NAME} fetch")

        raw_records = await self.fetch(**kwargs)
        logger.info(
            f"{self.SOURCE_NAME}: fetched {len(raw_records)} raw records"
        )

        normalised = []
        failed = 0

        for raw in raw_records:
            try:
                result = self.normalise(raw)
                if result is not None:
                    normalised.append(result)
            except Exception as e:
                failed += 1
                logger.error(
                    f"{self.SOURCE_NAME} normalise error: {e} "
                    f"raw={str(raw)[:200]}"
                )

        logger.info(
            f"{self.SOURCE_NAME}: normalised {len(normalised)} records "
            f"skipped={failed}"
        )

        return normalised