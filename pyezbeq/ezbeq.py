import logging
from types import TracebackType
from typing import Any, Dict, List, Optional, Type
from urllib.parse import quote

import httpx
from httpx import HTTPStatusError, RequestError
from pyezbeq.consts import DEFAULT_PORT, DEFAULT_SCHEME, DISCOVERY_ADDRESS
from pyezbeq.models import BeqCatalog, BeqDevice, SearchRequest
from pyezbeq.search import Search
from pyezbeq.errors import DeviceInfoEmpty, DataMismatch, BEQProfileNotFound


# ruff: noqa: E501
#
class EzbeqClient:
    def __init__(
        self,
        host: str = DISCOVERY_ADDRESS,
        port: int = DEFAULT_PORT,
        scheme: str = DEFAULT_SCHEME,
        logger: logging.Logger = logging.getLogger(__name__),
    ):
        self.server_url = f"{scheme}://{host}:{port}"
        self.current_profile = ""
        self.current_master_volume = 0.0
        self.current_media_type = ""
        self.mute_status = False
        self.master_volume = 0.0
        self.device_info: List[BeqDevice] = []
        self.search = Search(host=host, port=port, scheme=scheme)
        self.client = httpx.AsyncClient(timeout=30.0)
        self.logger = logger

    async def __aenter__(self) -> "EzbeqClient":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        await self.client.aclose()

    async def get_status(self) -> None:
        """Get the status of the ezbeq device."""
        try:
            response = await self.client.get(f"{self.server_url}/api/2/devices")
            response.raise_for_status()
        except HTTPStatusError as e:
            raise HTTPStatusError(
                f"Failed to get status: {e}", request=e.request, response=e.response
            ) from e
        except RequestError as e:
            raise RequestError(f"Failed to get status: {e}", request=e.request) from e

        data = response.json()
        self.logger.debug(f"Got status: {data}")
        self.device_info = [BeqDevice(**device) for device in data.values()]
        self.logger.debug(f"Device info: {self.device_info}")

        if not self.device_info:
            raise DeviceInfoEmpty("No devices found")

    async def mute_command(self, status: bool) -> None:
        """Set the mute status of the ezbeq device."""
        for device in self.device_info:
            method = "PUT" if status else "DELETE"
            url = f"{self.server_url}/api/1/devices/{quote(device.name)}/mute"
            try:
                response = await self.client.request(method, url)
                response.raise_for_status()
            except HTTPStatusError as e:
                raise HTTPStatusError(
                    f"Failed to set mute status for {device.name}: {e}",
                    request=e.request,
                    response=e.response,
                ) from e
            except RequestError as e:
                raise RequestError(
                    f"Failed to set mute status for {device.name}: {e}",
                    request=e.request,
                ) from e

            data = response.json()
            if data["mute"] != status:
                raise DataMismatch(f"Mute status mismatch for {device.name}")

    async def make_command(self, payload: Dict[str, Any]) -> None:
        """Send a command to the ezbeq device."""
        for device in self.device_info:
            url = f"{self.server_url}/api/1/devices/{quote(device.name)}"
            try:
                response = await self.client.patch(url, json=payload)
                response.raise_for_status()
            except HTTPStatusError as e:
                raise HTTPStatusError(
                    f"Failed to execute command for {device.name}: {e}",
                    request=e.request,
                    response=e.response,
                ) from e
            except RequestError as e:
                raise RequestError(
                    f"Failed to execute command for {device.name}: {e}",
                    request=e.request,
                ) from e

    async def load_beq_profile(self, search_request: SearchRequest) -> None:
        """Load a BEQ profile onto the ezbeq device."""
        if len(self.device_info) == 0:
            raise ValueError("No ezbeq devices provided. Can't load")

        # TODO: verify skip search
        if not search_request.skip_search:
            # exceptions caught with requestor
            catalog = await self.search.search_catalog(search_request)
            search_request.entry_id = catalog.id
            search_request.mvAdjust = catalog.mvAdjust
        else:
            catalog = BeqCatalog(
                id=search_request.entry_id,
                title="",
                sortTitle="",
                year=0,
                audioTypes=[],
                digest="",
                mvAdjust=search_request.mvAdjust,
                edition="",
                theMovieDB="",
                author="",
            )

        self.current_master_volume = search_request.mvAdjust
        self.current_profile = search_request.entry_id
        self.current_media_type = search_request.media_type

        if search_request.entry_id == "":
            raise BEQProfileNotFound("Could not find catalog entry for ezbeq")
        # TODO: implement dry run mode
        # if search_request.dry_run_mode:
        #     return f"BEQ Dry run msg - Would load title {catalog.title} -- codec {search_request.codec} -- edition: {catalog.edition}, ezbeq entry ID {search_request.entry_id} - author {catalog.author}"

        payload = {
            "slots": [
                {
                    "id": str(slot),
                    "gains": [search_request.mvAdjust, search_request.mvAdjust],
                    "active": True,
                    "mutes": [False, False],
                    "entry": search_request.entry_id,
                }
                for slot in (search_request.slots or [1])
            ]
        }

        for device in self.device_info:
            self.logger.debug(f"Loading BEQ profile for {device.name}")
            url = f"{self.server_url}/api/2/devices/{quote(device.name)}"
            try:
                response = await self.client.patch(url, json=payload)
                response.raise_for_status()
            except HTTPStatusError as e:
                raise HTTPStatusError(
                    f"Failed to load BEQ profile for {device}: {e}",
                    request=e.request,
                    response=e.response,
                ) from e
            except RequestError as e:
                raise RequestError(
                    f"Failed to load BEQ profile for {device}: {e}", request=e.request
                ) from e

    async def unload_beq_profile(self, search_request: SearchRequest) -> None:
        """Unload a BEQ profile from the ezbeq device."""
        if search_request.dry_run_mode:
            return

        for device in self.device_info:
            for slot in search_request.slots or [1]:
                url = f"{self.server_url}/api/1/devices/{quote(device.name)}/filter/{slot}"
                try:
                    response = await self.client.delete(url)
                    response.raise_for_status()
                except HTTPStatusError as e:
                    raise HTTPStatusError(
                        f"Failed to unload BEQ profile for {device.name}, slot {slot}: {e}",
                        request=e.request,
                        response=e.response,
                    ) from e
                except RequestError as e:
                    raise RequestError(
                        f"Failed to unload BEQ profile for {device.name}, slot {slot}: {e}",
                        request=e.request,
                    ) from e

    @staticmethod
    def url_encode(s: str) -> str:
        """URL encode a string."""
        return quote(s)
