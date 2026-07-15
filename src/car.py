from dataclasses import dataclass
from datetime import time, timedelta

NIGHT_SCHEDULE_START = time(2, 0)
NIGHT_SCHEDULE_END = time(5, 0)
MIDDAY_SCHEDULE_START = time(13,0)
MIDDAY_SCHEDULE_END = time(14,0)
OVERRIDE_DURATION = timedelta(minutes=60)
CHARGE_RATE_PER_30MIN = 0.05  # +5% SoC per 30-min slot (~10%/hr, typical Level 2 home charger)
LOOKAHEAD_HOURS = 24
PERIOD = timedelta(minutes=30)
INITIAL_SOC = 0.60


@dataclass
class MockCar:
    """
    Stateless representation of the physical car.
    Transient charge state (override timing, schedule suppression) lives in st.session_state,
    not here, because it belongs to the charging system, not the vehicle itself.
    """

    initial_soc: float = INITIAL_SOC
    charge_rate_per_30min: float = CHARGE_RATE_PER_30MIN
    max_soc: float = 1.0

    def current_soc(self) -> float:
        return self.initial_soc

    def is_in_schedule_window(self, t) -> bool:
        return (
            NIGHT_SCHEDULE_START <= t.time() < NIGHT_SCHEDULE_END 
            or MIDDAY_SCHEDULE_START <= t.time() < MIDDAY_SCHEDULE_END
        )