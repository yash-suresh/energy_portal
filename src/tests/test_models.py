from datetime import datetime

from models import ChargerState, CombinedState, DemoAdminState


def _t():
    return datetime(2024, 1, 15, 10, 0)


def test_demo_admin_state_fields():
    t = _t()
    s = DemoAdminState(car_is_plugged_in=True, current_time=t)
    assert s.car_is_plugged_in is True
    assert s.current_time == t


def test_charger_state_fields():
    s = ChargerState(car_is_charging=True, charge_is_override=False)
    assert s.car_is_charging is True
    assert s.charge_is_override is False


def test_combined_state_default_soc():
    s = CombinedState(time=_t(), charger_state=ChargerState(True, False))
    assert s.state_of_charge == 0.0


def test_combined_state_custom_soc():
    s = CombinedState(time=_t(), charger_state=ChargerState(True, False), state_of_charge=0.75)
    assert s.state_of_charge == 0.75
