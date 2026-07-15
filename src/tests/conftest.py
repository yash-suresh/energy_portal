from datetime import datetime
from unittest.mock import patch

import pytest


class SessionStateMock(dict):
    """Dict subclass with attribute-style access, mirroring st.session_state behaviour."""

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        del self[key]


@pytest.fixture
def session_state():
    """Patch streamlit.session_state and st.toast for all backend tests.

    Pre-populates the keys that backend.init_session_state() would set, mirroring
    what happens in the app at startup before any function is called.
    """
    mock_state = SessionStateMock()
    mock_state["override_start_time"] = None
    mock_state["schedule_disabled_until"] = None
    with patch("streamlit.session_state", mock_state), patch("streamlit.toast"):
        yield mock_state


@pytest.fixture
def night():
    """A datetime at 10pm — outside the 02:00–05:00 schedule window."""
    return datetime(2024, 1, 15, 22, 0)


@pytest.fixture
def in_schedule():
    """A datetime at 3am — inside the schedule window."""
    return datetime(2024, 1, 16, 3, 0)
