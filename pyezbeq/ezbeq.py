from types import TracebackType
from typing import Any, Dict, List, Optional, Type
from urllib.parse import quote

import httpx

from pyezbeq.consts import DEFAULT_PORT, DEFAULT_SCHEME, DISCOVERY_ADDRESS
from pyezbeq.models import BeqCatalog, BeqDevice, SearchRequest
from pyezbeq.search import Search


# ruff: noqa: E501
#
class EzbeqClient:
    def __init__(self, host: str = DISCOVERY_ADDRESS, port: int = DEFAULT_PORT, scheme: str = DEFAULT_SCHEME):
        self.server_url = f"{scheme}://{host}:{port}"
        self.current_profile = ""
        self.current_master_volume = 0.0
        self.current_media_type = ""
        self.mute_status = False
        self.master_volume = 0.0
        self.device_info: List[BeqDevice] = []
        self.search = Search(host=host, port=port, scheme=scheme)
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self) -> "EzbeqClient":
        return self

    async def __aexit__(
        self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[TracebackType]
    ) -> None:
        await self.client.aclose()

    async def get_status(self) -> None:
        response = await self.client.get(f"{self.server_url}/api/2/devices")
        if response.status_code == 200:
            data = response.json()
            self.device_info = [BeqDevice(**device) for device in data.values()]
        else:
            raise Exception("Failed to get status")

        if not self.device_info:
            raise Exception("No devices found")

    async def mute_command(self, status: bool) -> None:
        for device in self.device_info:
            method = "PUT" if status else "DELETE"
            url = f"{self.server_url}/api/1/devices/{quote(device.name)}/mute"
            response = await self.client.request(method, url)
            if response.status_code != 200:
                raise Exception(f"Failed to set mute status for {device.name}")
            data = response.json()
            if data["mute"] != status:
                raise Exception(f"Mute status mismatch for {device.name}")

    async def make_command(self, payload: Dict[str, Any]) -> None:
        for device in self.device_info:
            url = f"{self.server_url}/api/1/devices/{quote(device.name)}"
            response = await self.client.patch(url, json=payload)
            if response.status_code != 200:
                raise Exception(f"Failed to execute command for {device.name}")

    async def load_beq_profile(self, search_request: SearchRequest) -> None:
        if not search_request.devices:
            raise ValueError("No ezbeq devices provided. Can't load")

        if not search_request.skip_search:
            catalog = await self.search.search_catalog(search_request)
            search_request.entry_id = catalog.id
            search_request.mv_adjust = catalog.mv_adjust
        else:
            catalog = BeqCatalog(
                id=search_request.entry_id,
                title="",
                sort_title="",
                year=0,
                audio_types=[],
                digest="",
                mv_adjust=search_request.mv_adjust,
                edition="",
                movie_db_id="",
                author="",
            )

        self.current_master_volume = search_request.mv_adjust
        self.current_profile = search_request.entry_id
        self.current_media_type = search_request.media_type

        if search_request.entry_id == "":
            raise Exception("Could not find catalog entry for ezbeq")
        # TODO: implement dry run mode
        # if search_request.dry_run_mode:
        #     return f"BEQ Dry run msg - Would load title {catalog.title} -- codec {search_request.codec} -- edition: {catalog.edition}, ezbeq entry ID {search_request.entry_id} - author {catalog.author}"

        payload = {
            "slots": [
                {
                    "id": str(slot),
                    "gains": [search_request.mv_adjust, search_request.mv_adjust],
                    "active": True,
                    "mutes": [False, False],
                    "entry": search_request.entry_id,
                }
                for slot in (search_request.slots or [1])
            ]
        }

        for device in search_request.devices:
            url = f"{self.server_url}/api/2/devices/{quote(device)}"
            response = await self.client.patch(url, json=payload)
            if response.status_code != 200:
                raise Exception(f"Failed to load BEQ profile for {device}")

    async def unload_beq_profile(self, search_request: SearchRequest) -> None:
        if search_request.dry_run_mode:
            return

        for device in search_request.devices:
            for slot in search_request.slots or [1]:
                url = f"{self.server_url}/api/1/devices/{quote(device)}/filter/{slot}"
                response = await self.client.delete(url)
                if response.status_code != 200:
                    raise Exception(f"Failed to unload BEQ profile for {device}, slot {slot}")

    @staticmethod
    def url_encode(s: str) -> str:
        return quote(s)
