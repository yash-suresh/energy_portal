from datetime import datetime
from unittest.mock import patch

import pytest

from utils import get_current_time_to_nearest_30_minutes


def _mock_now(h, m, s=0, us=123456):
    return datetime(2024, 1, 15, h, m, s, us)


def _run(h, m, s=0):
    with patch("utils.datetime") as mock_dt:
        mock_dt.now.return_value = _mock_now(h, m, s)
        return get_current_time_to_nearest_30_minutes()


def test_rounds_down_at_14_minutes():
    result = _run(10, 14)
    assert result.hour == 10
    assert result.minute == 0


def test_rounds_up_at_16_minutes():
    result = _run(10, 16)
    assert result.hour == 10
    assert result.minute == 30


def test_at_exactly_30_minutes():
    result = _run(10, 30)
    assert result.hour == 10
    assert result.minute == 30


def test_at_exactly_0_minutes():
    result = _run(10, 0)
    assert result.hour == 10
    assert result.minute == 0


def test_rounds_up_at_45_minutes_wraps_hour():
    result = _run(10, 45)
    assert result.hour == 11
    assert result.minute == 0


def test_zeros_seconds_and_microseconds():
    result = _run(10, 14, s=45)
    assert result.second == 0
    assert result.microsecond == 0
