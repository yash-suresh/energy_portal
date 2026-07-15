from dataclasses import dataclass
from datetime import datetime


@dataclass
class DemoAdminState:
    """State we control from the admin panel to control the demo"""

    car_is_plugged_in: bool
    current_time: datetime


@dataclass
class ChargerState:
    """State of the car's charger"""

    car_is_charging: bool
    charge_is_override: bool


@dataclass
class CombinedState:
    """Helper class for grouping battery & charger data together"""

    time: datetime
    charger_state: ChargerState
    state_of_charge: float = 0.0
