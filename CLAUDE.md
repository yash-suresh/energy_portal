# Axle Energy Take-Home — Interview Prep

## Context
This is a take-home assignment for Axle Energy (EV charge control simulator). It was
built with Claude's help without the user (Yash) fully internalizing every design
decision. Axle has now invited Yash to an interview to discuss the solution and
potentially extend it live. This file tracks study progress and serves as a working
reference so future sessions can pick up where the last one left off.

Full brief: `briefing.pdf`. Design rationale already written up in `README.md`
("Assumptions" / "What I spent time on" / "What I considered less important" /
"System design" sections) — that doc is effectively the answer key for "why did you
do X" interview questions.

## What the app does
A Streamlit frontend for controlling EV home charging: shows current battery state,
a projected state-of-charge chart for the next 24h, and Start/Stop controls that
support a temporary 60-minute charge override on top of a fixed 02:00–05:00 schedule.

## Architecture (~400 lines total)
- `src/car.py` — `MockCar`: stateless physical vehicle model (SoC, charge rate,
  schedule window constants). No session state lives here on purpose.
- `src/backend.py` — charging control logic. Owns the state machine: override vs.
  scheduled charging vs. suppressed schedule. Reads/writes `st.session_state` for
  `override_start_time` and `schedule_disabled_until`. Core function to be able to
  trace by hand: `_is_charging_at()` (src/backend.py:38-51).
- `src/app.py` — UI layer (Streamlit). Demo admin controls (simulated clock,
  plugged-in toggle), status display, chart, Start/Stop buttons.
- `src/models.py` — dataclasses (`ChargerState`, `CombinedState`, `DemoAdminState`).
- `src/plotting.py` — builds the upcoming-charge chart.
- `src/utils.py` — small time-rounding helper.
- `src/tests/` — pytest suite (~500 lines) covering pure logic, stateful behavior,
  and integration; a good secondary source of "intended behavior" beyond the code.

Key edge cases to be fluent on:
- Stopping an override vs. stopping scheduled charging behave differently
  (`handle_stop_charge`, src/backend.py:116-125).
- Override auto-expiry at the 60-minute mark (src/backend.py:65-68).
- Schedule suppression until "tomorrow morning" after a manual stop
  (`_next_schedule_start`, src/backend.py:54-61).

## Interview prep plan
Estimated effort: 2–3 days of 5–6hr sessions (small codebase — could be done in
~1.5 focused days, but budget for rehearsal, not just reading).

**Day 1 — Understand**
- Re-read `briefing.pdf` and README's design-decision sections.
- Read every source file, then trace the state machine by hand for a few scenarios
  (override running → stop; scheduled charging → stop; override expiring mid-sim).
- Run via `docker compose up`, click every control, try edge times (exactly 02:00).
- Read the test suite for intended behavior.

**Day 2 — Get fluent**
- Re-implement `_is_charging_at` and `get_future_states` from memory, diff against
  the real code to find gaps in understanding.
- Rehearse answers (in own words) for: why `MockCar` is stateless, why session_state
  holds transient charge state, why 30-min slots, what changes for production
  (persistence, real car API, error handling).
- Cold-build 2-3 plausible extension features without assistance, e.g.: multiple/
  variable charge windows, dynamic tariff-based pricing signal, multi-car support,
  persisting session state to a DB. This is the highest-value rep for the live
  coding portion of the interview.

**Day 3 (buffer, optional)** — only if Day 2 cold-builds exposed gaps; otherwise one
more timed feature build to simulate interview pressure.

## Progress log
_(update this as study sessions happen)_
- 2026-07-09: Initial plan drafted. Codebase read and summarized above. No hands-on
  study session yet.
