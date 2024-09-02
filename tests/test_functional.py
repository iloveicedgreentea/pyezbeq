# type: ignore

import asyncio
import os

import pytest

from pyezbeq.models import SearchRequest

if not os.getenv("TEST_FUNCTIONAL"):
    pytest.skip("Skipping functional tests", allow_module_level=True)


@pytest.mark.asyncio
async def test_get_status(ezbeq_client):
    async with ezbeq_client:
        await ezbeq_client.get_status()

    assert len(ezbeq_client.device_info) > 0
    assert ezbeq_client.device_info[0].name is not None

@pytest.mark.asyncio
async def test_search_and_load_profile(ezbeq_client):
    search_request = SearchRequest(
        tmdb="51497",  # Fast Five
        year=2011,
        codec="DTS-X",
        preferred_author="",
        edition="Extended",
        slots=[1]
    )

    async with ezbeq_client:
        await ezbeq_client.get_status()
        # Search for the profile
        catalog = await ezbeq_client.search.search_catalog(search_request)
        assert catalog is not None
        assert catalog.title == "Fast Five"

        # Load the profile
        await ezbeq_client.load_beq_profile(search_request)
        assert ezbeq_client.current_profile is not None
        assert ezbeq_client.current_master_volume is not None
        await asyncio.sleep(1)  # Wait for the profile to load
        # Unload the profile
        await ezbeq_client.unload_beq_profile(search_request)

# @pytest.mark.asyncio
# async def test_mute_unmute(ezbeq_client):
#     async with ezbeq_client:
#         # Mute
#         await ezbeq_client.mute_command(True)
#         await ezbeq_client.get_status()
#         assert ezbeq_client.device_info[0].mute is True

#         # Unmute
#         await ezbeq_client.mute_command(False)
#         await ezbeq_client.get_status()
#         assert ezbeq_client.device_info[0].mute is False

# @pytest.mark.asyncio
# async def test_search_not_found(ezbeq_client):
#     search_request = SearchRequest(
#         tmdb="999999999",  # Non-existent TMDB ID
#         year=2099,
#         codec="FUTURE-CODEC",
#         preferred_author="",
#         edition="",
#         devices=["master"],
#         slots=[1]
#     )

#     async with ezbeq_client:
#         with pytest.raises(Exception, match="BEQ profile was not found in catalog"):
#             await ezbeq_client.search.search_catalog(search_request)
