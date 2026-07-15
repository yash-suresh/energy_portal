"""Tests for pure helper functions in backend.py — no Streamlit mocking needed."""
from datetime import datetime, timedelta

import pytest

from backend import (
    _is_charging_at,
    _next_schedule_start,
    _override_active_at,
    _schedule_disabled_at,
)

NIGHT = datetime(2024, 1, 15, 22, 0)       # 10pm — outside schedule window
IN_SCHEDULE = datetime(2024, 1, 16, 3, 0)  # 3am  — inside schedule window


# --- _override_active_at ---

def test_override_none_is_never_active():
    assert _override_active_at(NIGHT, None) is False


def test_override_before_start():
    start = NIGHT + timedelta(minutes=1)
    assert _override_active_at(NIGHT, start) is False


def test_override_at_start_is_active():
    assert _override_active_at(NIGHT, NIGHT) is True


def test_override_during_window():
    start = NIGHT - timedelta(minutes=30)
    assert _override_active_at(NIGHT, start) is True


def test_override_at_exact_end_is_not_active():
    # End is exclusive: override_start + 60min
    start = NIGHT - timedelta(minutes=60)
    assert _override_active_at(NIGHT, start) is False


def test_override_after_window():
    start = NIGHT - timedelta(minutes=90)
    assert _override_active_at(NIGHT, start) is False


# --- _schedule_disabled_at ---

def test_schedule_disabled_none_is_never_disabled():
    assert _schedule_disabled_at(NIGHT, None) is False


def test_schedule_disabled_before_until():
    disabled_until = NIGHT + timedelta(hours=1)
    assert _schedule_disabled_at(NIGHT, disabled_until) is True


def test_schedule_disabled_at_exactly_until():
    # disabled_until is exclusive: t < disabled_until
    assert _schedule_disabled_at(NIGHT, NIGHT) is False


def test_schedule_disabled_after_until():
    disabled_until = NIGHT - timedelta(hours=1)
    assert _schedule_disabled_at(NIGHT, disabled_until) is False


# --- _is_charging_at ---

def test_unplugged_never_charges():
    is_charging, is_override = _is_charging_at(IN_SCHEDULE, False, None, None)
    assert is_charging is False
    assert is_override is False


def test_override_active_outside_schedule_window():
    is_charging, is_override = _is_charging_at(NIGHT, True, NIGHT, None)
    assert is_charging is True
    assert is_override is True


def test_override_takes_priority_inside_schedule_window():
    is_charging, is_override = _is_charging_at(IN_SCHEDULE, True, IN_SCHEDULE, None)
    assert is_charging is True
    assert is_override is True


def test_scheduled_charge_no_override():
    is_charging, is_override = _is_charging_at(IN_SCHEDULE, True, None, None)
    assert is_charging is True
    assert is_override is False


def test_schedule_disabled_suppresses_charging():
    disabled_until = IN_SCHEDULE + timedelta(hours=1)
    is_charging, is_override = _is_charging_at(IN_SCHEDULE, True, None, disabled_until)
    assert is_charging is False
    assert is_override is False


def test_outside_window_not_charging():
    is_charging, is_override = _is_charging_at(NIGHT, True, None, None)
    assert is_charging is False
    assert is_override is False


# --- _next_schedule_start ---

def test_next_schedule_start_before_2am_same_day():
    t = datetime(2024, 1, 15, 1, 30)
    assert _next_schedule_start(t) == datetime(2024, 1, 15, 2, 0)


def test_next_schedule_start_at_midnight():
    t = datetime(2024, 1, 15, 0, 0)
    assert _next_schedule_start(t) == datetime(2024, 1, 15, 2, 0)


def test_next_schedule_start_at_2am_jumps_to_next_day():
    # Exactly at 2am — candidate == current_time, so we advance one day
    t = datetime(2024, 1, 15, 2, 0)
    assert _next_schedule_start(t) == datetime(2024, 1, 16, 2, 0)


def test_next_schedule_start_after_2am():
    t = datetime(2024, 1, 15, 14, 0)
    assert _next_schedule_start(t) == datetime(2024, 1, 16, 2, 0)


def test_next_schedule_start_during_schedule_window():
    t = datetime(2024, 1, 15, 3, 30)
    assert _next_schedule_start(t) == datetime(2024, 1, 16, 2, 0)
