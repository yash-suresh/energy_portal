"""End-to-end flow tests verifying the acceptance criteria from the brief."""
from datetime import datetime, timedelta

import pytest

import backend
from car import CHARGE_RATE_PER_30MIN, INITIAL_SOC, OVERRIDE_DURATION
from models import DemoAdminState


def make_demo(t: datetime, plugged_in: bool = True) -> DemoAdminState:
    return DemoAdminState(car_is_plugged_in=plugged_in, current_time=t)


NIGHT = datetime(2024, 1, 15, 22, 0)
SCHEDULE_3AM = datetime(2024, 1, 16, 3, 0)


def test_override_auto_reverts_after_60_minutes(session_state):
    """AC: after override duration elapses the car reverts to the schedule."""
    session_state["current_time"] = NIGHT
    backend.handle_start_charge()

    expired_time = NIGHT + OVERRIDE_DURATION + timedelta(minutes=1)
    state = backend.get_car_state(make_demo(expired_time))

    assert state.car_is_charging is False
    assert state.charge_is_override is False
    assert session_state.get("override_start_time") is None


def test_stop_override_does_not_affect_schedule(session_state):
    """AC: stopping an override reverts to schedule; schedule is not suppressed."""
    session_state["current_time"] = NIGHT
    backend.handle_start_charge()
    backend.handle_stop_charge()

    assert session_state.get("override_start_time") is None
    # Schedule should still fire at 3am
    state = backend.get_car_state(make_demo(SCHEDULE_3AM))
    assert state.car_is_charging is True
    assert state.charge_is_override is False


def test_stop_scheduled_charge_disables_rest_of_night(session_state):
    """AC: stopping scheduled charging disables the schedule until next morning."""
    session_state["current_time"] = SCHEDULE_3AM
    backend.handle_stop_charge()

    expected_disabled_until = datetime(2024, 1, 17, 2, 0)
    assert session_state.get("schedule_disabled_until") == expected_disabled_until

    # Remaining schedule window on Jan 16 (3am–5am) should produce no charging
    states = backend.get_future_states(make_demo(SCHEDULE_3AM))
    remaining_tonight = [
        s for s in states
        if datetime(2024, 1, 16, 3, 0) <= s.time < datetime(2024, 1, 16, 5, 0)
    ]
    assert remaining_tonight, "need at least one slot in remaining window"
    assert all(not s.charger_state.car_is_charging for s in remaining_tonight)


def test_full_schedule_soc_projection(session_state):
    """AC: SoC at end of schedule window equals initial + 6 slots × charge rate."""
    start = datetime(2024, 1, 15, 2, 0)
    states = backend.get_future_states(make_demo(start))
    # 6 slots of 30min from 2am → 5am; SoC is recorded before charging is applied
    # states[0]=2am (soc=0.60), states[6]=5am (soc after 6 charges)
    soc_at_5am = states[6].state_of_charge
    expected = INITIAL_SOC + 6 * CHARGE_RATE_PER_30MIN
    assert soc_at_5am == pytest.approx(expected)


def test_override_takes_priority_inside_schedule_window(session_state):
    """AC: an override that started before the schedule window keeps override status."""
    override_start = datetime(2024, 1, 15, 1, 30)  # 01:30 — 30min before schedule
    session_state["override_start_time"] = override_start

    states = backend.get_future_states(make_demo(override_start))

    slot_at_2am = next(s for s in states if s.time == datetime(2024, 1, 15, 2, 0))
    assert slot_at_2am.charger_state.car_is_charging is True
    assert slot_at_2am.charger_state.charge_is_override is True


def test_unplugged_car_is_never_charged(session_state):
    """AC: charging only occurs when plugged in."""
    session_state["override_start_time"] = NIGHT  # override active
    state = backend.get_car_state(make_demo(NIGHT, plugged_in=False))
    assert state.car_is_charging is False


def test_schedule_resumes_after_disabled_until(session_state):
    """Schedule is re-enabled exactly when disabled_until is reached."""
    disabled_until = datetime(2024, 1, 16, 2, 0)
    session_state["schedule_disabled_until"] = disabled_until

    # At disabled_until the schedule is active again
    state = backend.get_car_state(make_demo(disabled_until))
    assert state.car_is_charging is True
    assert state.charge_is_override is False
