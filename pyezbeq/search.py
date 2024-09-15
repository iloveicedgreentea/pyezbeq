"""Search for BEQ profiles in the catalog."""

import logging
from types import TracebackType
from typing import Optional, Type
from urllib.parse import quote

import httpx
from httpx import HTTPStatusError, RequestError
from pyezbeq.consts import DEFAULT_PORT, DEFAULT_SCHEME, DISCOVERY_ADDRESS
from pyezbeq.errors import BEQProfileNotFound
from .models import BeqCatalog, SearchRequest

# ruff: noqa: E501


class Search:
    """Search for BEQ profiles in the catalog."""

    def __init__(
        self,
        host: str = DISCOVERY_ADDRESS,
        port: int = DEFAULT_PORT,
        scheme: str = DEFAULT_SCHEME,
        logger: logging.Logger = logging.getLogger(__name__),
    ):
        self.server_url = f"{scheme}://{host}:{port}"
        self.logger = logger
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self) -> "Search":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        await self.client.aclose()

    async def search_catalog(self, search_request: SearchRequest) -> BeqCatalog:
        """Search the catalog for a BEQ profile."""
        codec = self.url_encode(search_request.codec)
        url = f"{self.server_url}/api/1/search?audiotypes={codec}&years={search_request.year}&tmdbid={search_request.tmdb}"

        if search_request.preferred_author:
            url = self._build_author_whitelist(search_request.preferred_author, url)
        try:
            response = await self.client.get(url)
            response.raise_for_status()
        except HTTPStatusError as e:
            raise HTTPStatusError(
                f"Failed to search BEQ catalog: {e}",
                request=e.request,
                response=e.response,
            ) from e
        except RequestError as e:
            raise RequestError(f"Failed to send request: {e}", request=e.request) from e
        data = response.json()

        for entry in data:
            if self._match_entry(entry, search_request):
                return BeqCatalog(**entry)

        raise BEQProfileNotFound("BEQ profile was not found in catalog")

    def _match_entry(self, entry: dict, search_request: SearchRequest) -> bool:
        self.logger.debug(f"Checking entry: {entry}")
        audio_match = any(
            codec.lower() == search_request.codec.lower()
            for codec in entry["audioTypes"]
        )
        # TODO: support search without TMDB?
        if (
            entry["theMovieDB"] == search_request.tmdb
            and entry["year"] == search_request.year
            and audio_match
        ):
            return self._check_edition(entry.get("edition", ""), search_request.edition)
        return False

    def _check_edition(self, beq_edition: str, request_edition: str) -> bool:
        if not beq_edition:
            return True
        return request_edition.lower() in beq_edition.lower()

    @staticmethod
    def _build_author_whitelist(preferred_authors: str, endpoint: str) -> str:
        for author in preferred_authors.split(","):
            endpoint += f"&authors={author.strip()}"
        return endpoint

    @staticmethod
    def url_encode(s: str) -> str:
        """Encode a string for use in a URL."""
        return quote(s)

    @staticmethod
    def has_author(s: str) -> bool:
        """Check if the author is set"""
        return s.lower().strip() not in ["none", ""]
