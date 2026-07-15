from datetime import datetime, time, timedelta

import pytest

from car import (
    CHARGE_RATE_PER_30MIN,
    INITIAL_SOC,
    LOOKAHEAD_HOURS,
    OVERRIDE_DURATION,
    PERIOD,
    NIGHT_SCHEDULE_END,
    NIGHT_SCHEDULE_START,
    MockCar,
)


def _dt(h, m=0):
    return datetime(2024, 1, 15, h, m)


# --- Constants ---

def test_constants():
    assert NIGHT_SCHEDULE_START == time(2, 0)
    assert NIGHT_SCHEDULE_END == time(5, 0)
    assert OVERRIDE_DURATION == timedelta(minutes=60)
    assert CHARGE_RATE_PER_30MIN == pytest.approx(0.05)
    assert INITIAL_SOC == pytest.approx(0.60)
    assert LOOKAHEAD_HOURS == 24
    assert PERIOD == timedelta(minutes=30)


# --- MockCar.current_soc ---

def test_current_soc_returns_initial():
    assert MockCar().current_soc() == pytest.approx(INITIAL_SOC)


def test_custom_initial_soc():
    assert MockCar(initial_soc=0.8).current_soc() == pytest.approx(0.8)


# --- MockCar.is_in_schedule_window ---

def test_is_in_schedule_window_during():
    assert MockCar().is_in_schedule_window(_dt(3)) is True


def test_is_in_schedule_window_at_start():
    assert MockCar().is_in_schedule_window(_dt(2, 0)) is True


def test_is_in_schedule_window_at_end():
    # 05:00 is the exclusive upper bound
    assert MockCar().is_in_schedule_window(_dt(5, 0)) is False


def test_is_in_schedule_window_just_before_start():
    assert MockCar().is_in_schedule_window(_dt(1, 59)) is False


def test_is_in_schedule_window_outside():
    assert MockCar().is_in_schedule_window(_dt(10)) is False
