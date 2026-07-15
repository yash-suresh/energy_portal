from __future__ import annotations

from datetime import datetime, timedelta

import streamlit as st

from car import (
    LOOKAHEAD_HOURS,
    OVERRIDE_DURATION,
    PERIOD,
    SCHEDULE_START,
    MockCar,
)
from models import ChargerState, CombinedState, DemoAdminState

_car = MockCar()


def init_session_state() -> None:
    if "override_start_time" not in st.session_state:
        st.session_state.override_start_time = None
    if "schedule_disabled_until" not in st.session_state:
        st.session_state.schedule_disabled_until = None


def _override_active_at(t: datetime, override_start: datetime | None) -> bool:
    if override_start is None:
        return False
    return override_start <= t < override_start + OVERRIDE_DURATION


def _schedule_disabled_at(t: datetime, disabled_until: datetime | None) -> bool:
    if disabled_until is None:
        return False
    return t < disabled_until


def _is_charging_at(
    t: datetime,
    car_is_plugged_in: bool,
    override_start: datetime | None,
    disabled_until: datetime | None,
) -> tuple[bool, bool]:
    """Return (car_is_charging, charge_is_override)."""
    if not car_is_plugged_in:
        return False, False
    if _override_active_at(t, override_start):
        return True, True
    if _car.is_in_schedule_window(t) and not _schedule_disabled_at(t, disabled_until):
        return True, False
    return False, False


def _next_schedule_start(current_time: datetime) -> datetime:
    """Return the next schedule start time after current_time."""
    candidate = current_time.replace(
        hour=SCHEDULE_START.hour, minute=SCHEDULE_START.minute, second=0, microsecond=0
    )
    if candidate <= current_time:
        candidate += timedelta(days=1)
    return candidate


def get_car_state(demo_state: DemoAdminState) -> ChargerState:
    # Auto-expire override when simulated time passes the 60-min mark
    if st.session_state.override_start_time is not None:
        if demo_state.current_time >= st.session_state.override_start_time + OVERRIDE_DURATION:
            st.session_state.override_start_time = None

    is_charging, is_override = _is_charging_at(
        demo_state.current_time,
        demo_state.car_is_plugged_in,
        st.session_state.override_start_time,
        st.session_state.schedule_disabled_until,
    )
    return ChargerState(car_is_charging=is_charging, charge_is_override=is_override)


def get_future_states(demo_state: DemoAdminState) -> list[CombinedState]:
    override_start = st.session_state.override_start_time
    disabled_until = st.session_state.schedule_disabled_until

    states: list[CombinedState] = []
    soc = _car.current_soc()
    t = demo_state.current_time
    end = demo_state.current_time + timedelta(hours=LOOKAHEAD_HOURS)

    while t < end:
        is_charging, is_override = _is_charging_at(
            t, demo_state.car_is_plugged_in, override_start, disabled_until
        )
        states.append(
            CombinedState(
                time=t,
                charger_state=ChargerState(
                    car_is_charging=is_charging, charge_is_override=is_override
                ),
                state_of_charge=soc,
            )
        )
        if is_charging:
            soc = min(soc + _car.charge_rate_per_30min, _car.max_soc)
        t += PERIOD

    return states


def handle_start_charge() -> None:
    current_time: datetime | None = st.session_state.get("current_time")
    if current_time is None:
        return
    st.session_state.override_start_time = current_time
    st.toast("Override started — charging for 60 minutes!", icon="⚡")


def handle_stop_charge() -> None:
    current_time: datetime | None = st.session_state.get("current_time")
    if current_time is None:
        return
    if _override_active_at(current_time, st.session_state.override_start_time):
        st.session_state.override_start_time = None
        st.toast("Override stopped — reverting to schedule.", icon="📅")
    else:
        st.session_state.schedule_disabled_until = _next_schedule_start(current_time)
        st.toast("Schedule disabled until tomorrow morning.", icon="🌙")
