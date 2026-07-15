from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
from plotly.graph_objs import Figure

from models import CombinedState

# These set the resampling period for graphing
PERIOD = timedelta(minutes=30)
PERIOD_STR = "30min"


def _convert_states_to_dataframe(states: list[CombinedState]) -> pd.DataFrame:
    """Convert to dataframe for ease of plotting with Plotly, and resample to 30mins"""
    if not states:
        return pd.DataFrame(
            columns=["Time", "State of Charge", "Car is Charging", "Charge is Override"]
        )
    df = pd.DataFrame(
        [
            {
                "Time": s.time,
                "State of Charge": s.state_of_charge,
                "Car is Charging": s.charger_state.car_is_charging,
                "Charge is Override": s.charger_state.charge_is_override,
            }
            for s in states
        ]
    )
    return df.reset_index()


def plot_upcoming_charges(
    states: list[CombinedState], current_time: datetime
) -> Figure:
    """Plot the upcoming charges for the car"""
    df = _convert_states_to_dataframe(states)
    fig = px.line(df, x="Time", y="State of Charge")

    # Add a vertical line at the current time
    fig.add_vline(
        x=current_time,
        line_dash="dash",
        line_color="white",
        label=dict(text="Now", textposition="top center"),
    )

    # Add vertical rectangles for charging periods
    for i, row in df.iterrows():
        if not row["Car is Charging"]:
            continue
        fig.add_vrect(
            x0=row["Time"],
            x1=row["Time"] + PERIOD,
            fillcolor="red" if row["Charge is Override"] else "green",
            opacity=0.1,
            layer="below",
            label=dict(
                text="Override" if row["Charge is Override"] else "Scheduled",
                font=dict(
                    color="red" if row["Charge is Override"] else "green",
                ),
                textposition="top center",
            ),
        )

    fig.update_traces(mode="markers+lines")
    return fig
