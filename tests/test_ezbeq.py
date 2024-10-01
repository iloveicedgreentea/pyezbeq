# type: ignore
from urllib.parse import quote

import pytest
from pytest_httpx import HTTPXMock

from pyezbeq.consts import DEFAULT_PORT, DEFAULT_SCHEME
from pyezbeq.ezbeq import EzbeqClient
from pyezbeq.models import BeqCatalog, BeqDevice, SearchRequest
from pyezbeq.search import Search

from .consts import TEST_IP, MOCK_RESPONSE


@pytest.mark.asyncio
async def test_mute_command(ezbeq_client: EzbeqClient, httpx_mock: HTTPXMock):
    ezbeq_client.device_info = [
        BeqDevice(name="master", masterVolume=0.0, mute=False, type="minidsp")
    ]

    httpx_mock.add_response(
        url=f"{DEFAULT_SCHEME}://{TEST_IP}:{DEFAULT_PORT}/api/1/devices/master/mute",
        method="PUT",
        json={"mute": True},
    )

    async with ezbeq_client:
        await ezbeq_client.mute_command(True)

    assert httpx_mock.get_request().method == "PUT"


@pytest.mark.asyncio
async def test_load_beq_profile(ezbeq_client: EzbeqClient, httpx_mock: HTTPXMock):
    search_request = SearchRequest(
        tmdb="51497",
        year=2011,
        codec="DTS-X",
        preferred_author="none",
        edition="Extended",
        slots=[1],
    )

    httpx_mock.add_response(
        url=f"{DEFAULT_SCHEME}://{TEST_IP}:{DEFAULT_PORT}/api/1/search?audiotypes=DTS-X&years=2011&tmdbid=51497&authors=none",
        json=[
            {
                "id": "bd4577c143e73851d6db0697e0940a8f34633eec_416",
                "title": "Fast Five",
                "sortTitle": "Fast Five",
                "year": 2011,
                "audioTypes": ["DTS-X"],
                "digest": "cd630eb58b05beb95ca47355c1d5014ea84e00ae8c8133573b77ee604cf7119c",
                "mvAdjust": -1.5,
                "edition": "Extended",
                "theMovieDB": "51497",
                "author": "aron7awol",
            }
        ],
    )

    httpx_mock.add_response(
        url=f"{DEFAULT_SCHEME}://{TEST_IP}:{DEFAULT_PORT}/api/2/devices/master",
        method="PATCH",
        json={},
    )
    httpx_mock.add_response(
        url=f"{DEFAULT_SCHEME}://{TEST_IP}:{DEFAULT_PORT}/api/2/devices/master2",
        method="PATCH",
        json={},
    )
    httpx_mock.add_response(
        url=f"{DEFAULT_SCHEME}://{TEST_IP}:{DEFAULT_PORT}/api/2/devices",
        method="GET",
        json=MOCK_RESPONSE,
    )

    async with ezbeq_client:
        await ezbeq_client.load_beq_profile(search_request)

    assert ezbeq_client.current_master_volume == -1.5


@pytest.mark.asyncio
async def test_unload_beq_profile(ezbeq_client: EzbeqClient, httpx_mock: HTTPXMock):
    search_request = SearchRequest(
        tmdb="51497",
        year=2011,
        codec="DTS-X",
        preferred_author="none",
        edition="Extended",
        slots=[1],
    )

    httpx_mock.add_response(
        url=f"{DEFAULT_SCHEME}://{TEST_IP}:{DEFAULT_PORT}/api/1/devices/master/filter/1",
        method="DELETE",
        json={},
    )
    httpx_mock.add_response(
        url=f"{DEFAULT_SCHEME}://{TEST_IP}:{DEFAULT_PORT}/api/1/devices/master2/filter/1",
        method="DELETE",
        json={},
    )
    httpx_mock.add_response(
        url=f"{DEFAULT_SCHEME}://{TEST_IP}:{DEFAULT_PORT}/api/2/devices",
        method="GET",
        json=MOCK_RESPONSE,
    )

    async with ezbeq_client:
        await ezbeq_client.unload_beq_profile(search_request)
    for r in httpx_mock.get_requests()[0:2]:
        assert r.method == "DELETE"


@pytest.mark.asyncio
async def test_search_catalog(search_client: Search, httpx_mock: HTTPXMock):
    search_requests = [
        SearchRequest(
            tmdb="51497",
            year=2011,
            codec="DTS-X",
            preferred_author="",
            edition="Extended",
        ),
        SearchRequest(
            tmdb="843794", year=2023, codec="DD+ Atmos", preferred_author="", edition=""
        ),
        SearchRequest(
            tmdb="429351",
            year=2018,
            codec="DTS-HD MA 7.1",
            preferred_author="aron7awol",
            edition="",
        ),
        SearchRequest(
            tmdb="56292", year=2011, codec="TrueHD 7.1", preferred_author="", edition=""
        ),
    ]

    expected_results = [
        {
            "digest": "cd630eb58b05beb95ca47355c1d5014ea84e00ae8c8133573b77ee604cf7119c",
            "mvAdjust": -1.5,
        },
        {
            "digest": "1678d7860ead948132f70ba3d823d7493bb3bb79302f308d135176bf4ff6f7d0",
            "mvAdjust": 0.0,
        },
        {
            "digest": "c694bb4c1f67903aebc51998cd1aae417983368e784ed04bf92d873ee1ca213d",
            "mvAdjust": -3.5,
        },
        {
            "digest": "f7e8c32e58b372f1ea410165607bc1f6b3f589a832fda87edaa32a17715438f7",
            "mvAdjust": 0.0,
        },
    ]

    for request, expected in zip(search_requests, expected_results):
        url = f"{DEFAULT_SCHEME}://{TEST_IP}:{DEFAULT_PORT}/api/1/search?audiotypes={quote(request.codec)}&years={request.year}&tmdbid={request.tmdb}"
        if request.preferred_author:
            url += f"&authors={quote(request.preferred_author)}"

        httpx_mock.add_response(
            url=url,
            json=[
                {
                    "id": "test_id",
                    "title": "Test Movie",
                    "sortTitle": "Test Movie",
                    "year": request.year,
                    "audioTypes": [request.codec],
                    "digest": expected["digest"],
                    "mvAdjust": expected["mvAdjust"],
                    "edition": request.edition,
                    "theMovieDB": request.tmdb,
                    "author": "Test Author",
                }
            ],
        )

    async with search_client:
        for request, expected in zip(search_requests, expected_results):
            result = await search_client.search_catalog(request)
            assert isinstance(result, BeqCatalog)
            assert result.digest == expected["digest"]
            assert result.mvAdjust == expected["mvAdjust"]


@pytest.mark.asyncio
async def test_search_catalog_not_found(search_client: Search, httpx_mock: HTTPXMock):
    search_request = SearchRequest(
        tmdb="invalid_id",
        year=2018,
        codec="DTS-HD MA 5.1",
        preferred_author="",
        edition="",
    )

    httpx_mock.add_response(
        url=f"{DEFAULT_SCHEME}://{TEST_IP}:{DEFAULT_PORT}/api/1/search?audiotypes={quote(search_request.codec)}&years={search_request.year}&tmdbid={search_request.tmdb}",
        json=[],
    )

    async with search_client:
        with pytest.raises(Exception, match="BEQ profile was not found in catalog"):
            await search_client.search_catalog(search_request)


@pytest.mark.asyncio
async def test_load_profile_sequence(ezbeq_client: EzbeqClient, httpx_mock: HTTPXMock):
    test_cases = [
        SearchRequest(
            tmdb="51497",
            year=2011,
            codec="DTS-X",
            preferred_author="",
            edition="Extended",
            slots=[1],
        ),
        SearchRequest(
            tmdb="56292",
            year=2011,
            codec="AtmosMaybe",
            preferred_author="",
            edition="",
            slots=[1],
        ),
        SearchRequest(
            tmdb="399579",
            year=2019,
            codec="AtmosMaybe",
            preferred_author="",
            edition="",
            slots=[1],
        ),
        SearchRequest(
            tmdb="443791",
            year=2020,
            codec="DD+Atmos5.1Maybe",
            preferred_author="",
            edition="",
            slots=[1],
        ),
        SearchRequest(
            tmdb="804095",
            year=2022,
            codec="DD+Atmos7.1Maybe",
            preferred_author="",
            edition="",
            slots=[1],
        ),
    ]
    async with ezbeq_client:
        for case in test_cases:
            # Mock the search response
            search_url = f"{DEFAULT_SCHEME}://{TEST_IP}:{DEFAULT_PORT}/api/1/search?audiotypes={quote(case.codec)}&years={case.year}&tmdbid={case.tmdb}"
            httpx_mock.add_response(
                url=search_url,
                json=[
                    {
                        "id": f"test_id_{case.tmdb}",
                        "title": "Test Movie",
                        "sortTitle": "Test Movie",
                        "year": case.year,
                        "audioTypes": [case.codec],
                        "digest": "test_digest",
                        "mvAdjust": -1.5,
                        "edition": case.edition,
                        "theMovieDB": case.tmdb,
                        "author": "Test Author",
                    }
                ],
            )
            httpx_mock.add_response(
                url=f"{DEFAULT_SCHEME}://{TEST_IP}:{DEFAULT_PORT}/api/2/devices",
                method="GET",
                json=MOCK_RESPONSE,
            )
            # Mock the load profile response
            for device in ezbeq_client.device_info:
                load_url = f"{DEFAULT_SCHEME}://{TEST_IP}:{DEFAULT_PORT}/api/2/devices/{device.name}"
                httpx_mock.add_response(url=load_url, method="PATCH", json={})

            # Mock the unload profile response
            for device in ezbeq_client.device_info:
                for slot in case.slots:
                    unload_url = f"{DEFAULT_SCHEME}://{TEST_IP}:{DEFAULT_PORT}/api/1/devices/{device.name}/filter/{slot}"
                    httpx_mock.add_response(url=unload_url, method="DELETE", json={})

            # Load profile
            await ezbeq_client.load_beq_profile(case)
            for device in ezbeq_client.device_info:
                assert ezbeq_client.get_device_profile(device.name) == "Fast Five"
                assert device.masterVolume == -1.5

            # Unload profile
            await ezbeq_client.unload_beq_profile(case)


def test_url_encode():
    assert EzbeqClient.url_encode("DTS-HD MA 7.1") == "DTS-HD%20MA%207.1"


@pytest.mark.parametrize(
    "author,expected",
    [
        ("aron7awol", True),
        ("None", False),
        (" ", False),
        ("", False),
        ("none", False),
        ("aron7awol, mobe1969", True),
    ],
)
def test_has_author(author, expected):
    assert Search.has_author(author) == expected


def test_build_author_whitelist():
    base_url = "/api/1/search?audiotypes=dts-x&years=2011&tmdbid=12345"
    result = Search._build_author_whitelist("aron7awol, mobe1969", base_url)
    assert (
        result
        == "/api/1/search?audiotypes=dts-x&years=2011&tmdbid=12345&authors=aron7awol&authors=mobe1969"
    )
