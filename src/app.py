import streamlit as st

import backend
from car import INITIAL_SOC, NIGHT_SCHEDULE_END, NIGHT_SCHEDULE_START, MIDDAY_SCHEDULE_START, MIDDAY_SCHEDULE_END
from models import ChargerState, CombinedState, DemoAdminState
from plotting import plot_upcoming_charges
from utils import get_current_time_to_nearest_30_minutes


def get_demo_state() -> DemoAdminState:
    rounded_time = get_current_time_to_nearest_30_minutes()
    with st.sidebar:
        st.subheader("Demo Admin Controls")
        st.write("Use these controls to simulate the car and charger state.")

        current_time = st.time_input("Current Time", rounded_time)
        # Add back in the date to the time
        current_time = rounded_time.replace(
            hour=current_time.hour, minute=current_time.minute
        )

        car_is_plugged_in = st.toggle("Plugged in", value=True)

    return DemoAdminState(
        car_is_plugged_in=car_is_plugged_in, current_time=current_time
    )


def _projected_end_soc(future_states: list[CombinedState]) -> float:
    """SoC at the end of the next scheduled charge window."""
    for i, s in enumerate(future_states):
        t = s.time.time()
        if t == NIGHT_SCHEDULE_END:
            return s.state_of_charge
        if i > 0 and t > NIGHT_SCHEDULE_END and future_states[i - 1].time.time() < NIGHT_SCHEDULE_END:
            return s.state_of_charge
    return INITIAL_SOC


def show_status(
    demo_state: DemoAdminState,
    car_state: ChargerState,
    future_states: list[CombinedState],
) -> None:
    projected_soc = _projected_end_soc(future_states)

    if not demo_state.car_is_plugged_in:
        connection_label = "Not connected"
        status_label = "Unplugged"
    elif car_state.charge_is_override:
        connection_label = "Connected"
        status_label = "Charging (Override)"
    elif car_state.car_is_charging:
        connection_label = "Connected"
        status_label = "Charging (Scheduled)"
    else:
        connection_label = "Connected"
        status_label = "Idle"

    schedule_end_label = NIGHT_SCHEDULE_END.strftime("%I%p").lstrip("0").lower()
    window_label = (
        f"{NIGHT_SCHEDULE_START.strftime('%H:%M')} – {NIGHT_SCHEDULE_END.strftime('%H:%M')}"
    )
    second_label = (
        f"{MIDDAY_SCHEDULE_START.strftime('%H:%M')} – {MIDDAY_SCHEDULE_END.strftime('%H:%M')}"
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Battery", f"{INITIAL_SOC:.0%}")
    col2.metric(f"After Schedule ({schedule_end_label})", f"{projected_soc:.0%}")
    col3.metric("Connection", connection_label)
    col4.metric("Status", status_label)

    st.info(f"Scheduled charging window: {window_label} and {second_label} daily")


def controls(car_is_plugged_in: bool, car_is_charging: bool, charge_is_override: bool):
    st.subheader("Controls")
    c1, c2 = st.columns([1, 1])

    start_disabled = not car_is_plugged_in or charge_is_override
    stop_label = "Stop Override" if charge_is_override else "Stop Charge"
    stop_disabled = not car_is_charging

    if not car_is_plugged_in:
        st.warning("Car is not plugged in — connect the cable to enable charging.", icon="🔌")

    return (
        c1.button("Start Charge", disabled=start_disabled, on_click=backend.handle_start_charge),
        c2.button(stop_label, disabled=stop_disabled, on_click=backend.handle_stop_charge),
    )


if __name__ == "__main__":
    st.title("Charge Control Panel")

    backend.init_session_state()

    demo_state = get_demo_state()

    # Must be set before controls render so on_click callbacks can read it
    st.session_state["current_time"] = demo_state.current_time

    car_state = backend.get_car_state(demo_state)
    future_states = backend.get_future_states(demo_state)

    show_status(demo_state, car_state, future_states)

    st.subheader("Charging Schedule")
    st.plotly_chart(
        plot_upcoming_charges(future_states, current_time=demo_state.current_time)
    )

    controls(
        demo_state.car_is_plugged_in,
        car_state.car_is_charging,
        car_state.charge_is_override,
    )
