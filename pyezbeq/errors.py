"""Errors for madvr"""

from __future__ import annotations


class RetryExceededError(Exception):
    """Too many retries"""


class HeartBeatError(Exception):
    """An error has occured with heartbeats"""


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class DeviceInfoEmpty(Exception):
    """Error to indicate device info is empty."""


class DataMismatch(Exception):
    """Error to indicate data mismatch."""


class BEQProfileNotFound(Exception):
    """Error to indicate BEQ profile was not found in catalog."""
