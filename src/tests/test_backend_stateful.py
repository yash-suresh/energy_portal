"""Tests for backend functions that read/write st.session_state."""
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

import backend
from car import CHARGE_RATE_PER_30MIN, INITIAL_SOC, LOOKAHEAD_HOURS, OVERRIDE_DURATION
from models import ChargerState, DemoAdminState


def make_demo(t: datetime, plugged_in: bool = True) -> DemoAdminState:
    return DemoAdminState(car_is_plugged_in=plugged_in, current_time=t)


NIGHT = datetime(2024, 1, 15, 22, 0)       # 10pm — outside schedule window
SCHEDULE_3AM = datetime(2024, 1, 16, 3, 0)  # 3am  — inside schedule window


# --- get_car_state ---

def test_idle_outside_schedule(session_state):
    state = backend.get_car_state(make_demo(NIGHT))
    assert state == ChargerState(car_is_charging=False, charge_is_override=False)


def test_scheduled_charging(session_state):
    state = backend.get_car_state(make_demo(SCHEDULE_3AM))
    assert state == ChargerState(car_is_charging=True, charge_is_override=False)


def test_override_active(session_state):
    session_state["override_start_time"] = NIGHT
    state = backend.get_car_state(make_demo(NIGHT))
    assert state == ChargerState(car_is_charging=True, charge_is_override=True)


def test_override_auto_expires(session_state):
    session_state["override_start_time"] = NIGHT
    expired_time = NIGHT + OVERRIDE_DURATION + timedelta(minutes=1)

    state = backend.get_car_state(make_demo(expired_time))

    assert state == ChargerState(car_is_charging=False, charge_is_override=False)
    assert session_state.get("override_start_time") is None


def test_schedule_disabled_suppresses_charging(session_state):
    session_state["schedule_disabled_until"] = datetime(2024, 1, 17, 2, 0)
    state = backend.get_car_state(make_demo(SCHEDULE_3AM))
    assert state == ChargerState(car_is_charging=False, charge_is_override=False)


def test_unplugged_does_not_charge(session_state):
    state = backend.get_car_state(make_demo(SCHEDULE_3AM, plugged_in=False))
    assert state == ChargerState(car_is_charging=False, charge_is_override=False)


# --- get_future_states ---

def test_returns_48_slots(session_state):
    states = backend.get_future_states(make_demo(NIGHT))
    assert len(states) == LOOKAHEAD_HOURS * 2


def test_soc_increases_during_schedule(session_state):
    start = datetime(2024, 1, 15, 2, 0)
    states = backend.get_future_states(make_demo(start))
    soc_at_2am = states[0].state_of_charge
    soc_at_5am = states[6].state_of_charge  # 6 × 30min = 5am
    assert soc_at_5am > soc_at_2am


def test_soc_capped_at_max(session_state):
    with patch("backend._car") as mock_car:
        mock_car.current_soc.return_value = 0.99
        mock_car.charge_rate_per_30min = 0.05
        mock_car.max_soc = 1.0
        mock_car.is_in_schedule_window.side_effect = lambda t: (
            t.time().hour >= 2 and t.time().hour < 5
        )
        states = backend.get_future_states(make_demo(datetime(2024, 1, 15, 2, 0)))
    assert all(s.state_of_charge <= 1.0 for s in states)


def test_override_slots_flagged_correctly(session_state):
    session_state["override_start_time"] = NIGHT
    states = backend.get_future_states(make_demo(NIGHT))
    override_slots = [s for s in states if s.charger_state.charge_is_override]
    # OVERRIDE_DURATION = 60min → exactly 2 × 30min slots
    assert len(override_slots) == 2


def test_unplugged_produces_no_charging_slots(session_state):
    states = backend.get_future_states(make_demo(NIGHT, plugged_in=False))
    assert all(not s.charger_state.car_is_charging for s in states)


def test_schedule_disabled_suppresses_scheduled_slots(session_state):
    session_state["schedule_disabled_until"] = datetime(2024, 1, 17, 2, 0)
    states = backend.get_future_states(make_demo(SCHEDULE_3AM))
    window = [
        s for s in states
        if datetime(2024, 1, 16, 3, 0) <= s.time < datetime(2024, 1, 16, 5, 0)
    ]
    assert window, "expected slots in the schedule window within the 24hr lookahead"
    assert all(not s.charger_state.car_is_charging for s in window)


# --- handle_start_charge ---

def test_start_charge_sets_override_start_time(session_state):
    session_state["current_time"] = NIGHT
    backend.handle_start_charge()
    assert session_state.get("override_start_time") == NIGHT


def test_start_charge_without_current_time_is_noop(session_state):
    backend.handle_start_charge()
    assert session_state.get("override_start_time") is None


# --- handle_stop_charge ---

def test_stop_charge_clears_active_override(session_state):
    session_state["override_start_time"] = NIGHT
    session_state["current_time"] = NIGHT
    backend.handle_stop_charge()
    assert session_state.get("override_start_time") is None


def test_stop_scheduled_charge_disables_schedule(session_state):
    session_state["current_time"] = SCHEDULE_3AM  # 3am Jan 16
    backend.handle_stop_charge()
    # _next_schedule_start(3am Jan 16) = 2am Jan 17
    assert session_state.get("schedule_disabled_until") == datetime(2024, 1, 17, 2, 0)


def test_stop_outside_window_sets_disabled_until(session_state):
    session_state["current_time"] = NIGHT  # 10pm Jan 15
    backend.handle_stop_charge()
    # _next_schedule_start(10pm Jan 15) = 2am Jan 16
    assert session_state.get("schedule_disabled_until") == datetime(2024, 1, 16, 2, 0)
