import pytest

from pyezbeq.ezbeq import EzbeqClient
from pyezbeq.search import Search

from .consts import TEST_IP


@pytest.fixture
def ezbeq_client() -> EzbeqClient:
    return EzbeqClient(host=TEST_IP)


@pytest.fixture
def search_client() -> Search:
    return Search(host=TEST_IP)
