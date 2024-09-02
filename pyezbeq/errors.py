"""Errors for madvr"""

from __future__ import annotations


class RetryExceededError(Exception):
    """Too many retries"""


class HeartBeatError(Exception):
    """An error has occured with heartbeats"""


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""
