import pytest

from pyezbeq.ezbeq import EzbeqClient
from pyezbeq.models import BeqDevice, BeqSlot
from pyezbeq.search import Search

from .consts import TEST_IP

# Mock device data
MOCK_DEVICE_INFO = [
    BeqDevice(
        name="master",
        masterVolume=-10.0,
        mute=False,
        slots=[BeqSlot(id="1", last="", active=False, gain1=0.0, gain2=0.0, mute1=False, mute2=False)],
        type="minidsp",
    ),
    BeqDevice(
        name="master2",
        masterVolume=-5.0,
        mute=False,
        slots=[BeqSlot(id="1", last="", active=False, gain1=0.0, gain2=0.0, mute1=False, mute2=False)],
        type="minidsp",
    ),
]


@pytest.fixture
def ezbeq_client() -> EzbeqClient:
    client = EzbeqClient(host=TEST_IP)

    client.device_info = MOCK_DEVICE_INFO

    return client


@pytest.fixture
def search_client() -> Search:
    return Search(host=TEST_IP)
