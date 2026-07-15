from datetime import datetime

import pytest
from plotly.graph_objs import Figure

from models import ChargerState, CombinedState
from plotting import _convert_states_to_dataframe, plot_upcoming_charges

BASE_TIME = datetime(2024, 1, 15, 2, 0)


def make_state(h, m=0, charging=False, override=False, soc=0.6):
    return CombinedState(
        time=datetime(2024, 1, 15, h, m),
        charger_state=ChargerState(car_is_charging=charging, charge_is_override=override),
        state_of_charge=soc,
    )


# --- _convert_states_to_dataframe ---

def test_empty_states_returns_empty_dataframe():
    df = _convert_states_to_dataframe([])
    assert len(df) == 0
    for col in ("Time", "State of Charge", "Car is Charging", "Charge is Override"):
        assert col in df.columns


def test_converts_states_to_dataframe_correctly():
    states = [
        make_state(2, soc=0.6),
        make_state(2, 30, charging=True, soc=0.65),
    ]
    df = _convert_states_to_dataframe(states)
    assert len(df) == 2
    assert df["State of Charge"].iloc[0] == pytest.approx(0.6)
    assert df["State of Charge"].iloc[1] == pytest.approx(0.65)
    assert df["Car is Charging"].iloc[0] == False  # noqa: E712 — np.False_ != False with `is`
    assert df["Car is Charging"].iloc[1] == True  # noqa: E712


def test_override_column_mapped_correctly():
    states = [make_state(2, charging=True, override=True, soc=0.6)]
    df = _convert_states_to_dataframe(states)
    assert df["Charge is Override"].iloc[0] == True  # noqa: E712


# --- plot_upcoming_charges ---

def test_plot_returns_plotly_figure():
    states = [make_state(2, soc=0.6), make_state(2, 30, charging=True, soc=0.65)]
    fig = plot_upcoming_charges(states, BASE_TIME)
    assert isinstance(fig, Figure)


def test_plot_contains_vline_for_current_time():
    states = [make_state(2, soc=0.6)]
    fig = plot_upcoming_charges(states, BASE_TIME)
    vlines = [s for s in fig.layout.shapes if s.type == "line"]
    assert len(vlines) >= 1


def test_plot_scheduled_charging_slot_has_green_vrect():
    states = [make_state(2, charging=True, override=False, soc=0.6)]
    fig = plot_upcoming_charges(states, BASE_TIME)
    vrects = [s for s in fig.layout.shapes if s.type == "rect"]
    assert len(vrects) >= 1
    assert any(s.fillcolor == "green" for s in vrects)


def test_plot_override_charging_slot_has_red_vrect():
    states = [make_state(2, charging=True, override=True, soc=0.6)]
    fig = plot_upcoming_charges(states, BASE_TIME)
    vrects = [s for s in fig.layout.shapes if s.type == "rect"]
    assert len(vrects) >= 1
    assert any(s.fillcolor == "red" for s in vrects)


def test_plot_non_charging_slot_has_no_vrect():
    states = [make_state(2, charging=False, soc=0.6)]
    fig = plot_upcoming_charges(states, BASE_TIME)
    vrects = [s for s in fig.layout.shapes if s.type == "rect"]
    assert len(vrects) == 0
