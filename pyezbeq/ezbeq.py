import logging
from types import TracebackType
from typing import Any, Dict, List, Optional, Type
from urllib.parse import quote

import httpx
from httpx import HTTPStatusError, RequestError
from pyezbeq.consts import DEFAULT_PORT, DEFAULT_SCHEME, DISCOVERY_ADDRESS
from pyezbeq.models import BeqCatalog, BeqDevice, SearchRequest, BeqSlot
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
        self.version = ""

    async def __aenter__(self) -> "EzbeqClient":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        await self.client.aclose()

    async def get_version(self) -> str:
        """Get the version of the ezbeq device."""
        try:
            response = await self.client.get(f"{self.server_url}/api/1/version")
            response.raise_for_status()
        except HTTPStatusError as e:
            raise HTTPStatusError(
                f"Failed to get version: {e}", request=e.request, response=e.response
            ) from e
        except RequestError as e:
            raise RequestError(f"Failed to get version: {e}", request=e.request) from e

        resp = response.json().get("version")
        self.version = resp
        return resp

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

        data: Dict[str, Any] = response.json()
        self.logger.debug(f"Got status: {data}")
        self.update_device_data(data)
        self.logger.debug("Device info: %s", self.device_info)

        if not self.device_info:
            raise DeviceInfoEmpty("No devices found")

    def update_device_data(self, data: Dict[str, Any]) -> None:
        """Refresh internal state with new device data."""
        self.device_info = [self.create_beq_device(device) for device in data.values()]
        self.current_profile = self.find_current_profile(self.device_info)

    def create_beq_device(self, device_data: Dict[str, Any]) -> BeqDevice:
        """Create a BEQ device from the device data."""
        slots = [
            BeqSlot(
                id=slot["id"],
                last=slot["last"],
                active=slot["active"],
                gain1=slot["gains"][0]["value"],
                gain2=slot["gains"][1]["value"],
                mute1=slot["mutes"][0]["value"],
                mute2=slot["mutes"][1]["value"],
            )
            for slot in device_data["slots"]
        ]

        return BeqDevice(
            name=device_data["name"],
            mute=device_data["mute"],
            type=device_data["type"],
            masterVolume=device_data["masterVolume"],
            slots=slots,
        )

    def find_current_profile(self, device_info: List[BeqDevice]) -> str:
        """Find the current profile name."""
        for device in device_info:
            self.logger.debug(
                f"Checking device {device.name} with slots {device.slots}"
            )
            for slot in device.slots:
                if slot.last:
                    self.logger.debug("Found profile %s", slot.last)
                    return slot.last
        return ""

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
        # refresh status
        await self.get_status()

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
        # refresh status
        await self.get_status()

    @staticmethod
    def url_encode(s: str) -> str:
        """URL encode a string."""
        return quote(s)
