# Axle Engineering Takehome
Find the full briefing [here](briefing.pdf).

We've provided a minimal frontend for you to integrate with. 

## Running the frontend

You'll need Docker installed.

`docker compose up`

You can then access the frontend at [http://localhost:8501/]()

We've added some dummy data so you can see what the end result will look like.

## Adding your code

Your code should interface with the existing frontend via the `backend.py` module.

You are free to write whatever code you like (inside this service, or adding new ones). 

Feel free to expand upon the frontend if there are features that you feel are missing, or you want to change how state is handled.

## Design decisions

### Assumptions
- **Starting SoC is hardcoded at 60%.** In production this would come from the car's API. I used a constant so the mock stays simple and easy to change.
- **Charge schedule is fixed at 02:00–05:00.** The briefing says to mock this with something reasonable — I chose a typical off-peak window. A real system would fetch this from a pricing or grid signal API.
- **Charge rate is 5% SoC per 30-minute slot (~10%/hr).** This approximates a standard Level 2 home charger. It's a constant on `MockCar` so it's easy to adjust.
- **Override duration is 60 minutes.** The briefing gives this as an example; I treated it as a hard requirement.
- **The simulation runs in 30-minute slots.** This matches the typical granularity of energy tariffs and keeps the chart readable.

### What I spent time on
- **Correctness of the stop/override logic.** The interaction between override state, schedule suppression, and the stop button has a few edge cases (e.g. stopping an override vs. stopping scheduled charging behave differently). I made sure these were well-separated and tested mentally against all states.
- **Keeping car state and charging system state separate.** `MockCar` is stateless — it only knows about the vehicle's physical properties. Transient charging state (override timing, schedule suppression) lives in `st.session_state` because it belongs to the charging controller, not the car.
- **A clear, self-explanatory UI.** The target user is a non-technical homeowner. I kept the layout to a single screen with plain-English labels, a chart showing future SoC, and explicit feedback (toasts, warnings) for every action.

### What I considered less important
- **Persistence across browser refreshes.** `st.session_state` is in-memory, so state resets on refresh. For a production app you'd back this with a database or cache. I didn't add this since the brief asked for a mock.
- **Mobile layout optimisation.** Streamlit's column layout works on mobile but isn't optimised for it. The brief said either was fine.
- **Error handling for the car API.** Since the car is mocked, I didn't add retry logic or error states for failed API calls.

### System design
The app is split into three layers: `car.py` (physical vehicle model), `backend.py` (charging control logic), and `app.py` (UI). This mirrors how a real system would be structured — the car, the controller, and the interface are separate concerns. `MockCar` can be swapped for a real API client without touching the UI or control logic.
