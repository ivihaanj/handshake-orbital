# Ground Station Dashboard (prototype)

A single-demo prototype to click through and validate the idea: real
satellite pass prediction + a dashboard UI + a mock live-telemetry preview.

Not production-grade — TLEs are hardcoded, telemetry is fake, there's no
auth or persistence. It's meant to be shown around, not deployed.

## What's real vs. fake

- **Real**: satellite positions, pass times, elevations, and the ground
  track. These come from [Skyfield](https://rhodesmill.org/skyfield/),
  which runs the same SGP4 orbit-propagation model real ground stations
  use, fed with live TLE data pulled from
  [Celestrak](https://celestrak.org) for the ISS, NOAA 20, and NOAA 15.
- **Fake**: the "Mock live telemetry" panel (battery/temperature/signal).
  It's a random walk in the browser, just to preview what a live-pass
  screen could look like. No backend involved in that part.

## Setup

Requires Python 3.9+.

```bash
python3 -m venv .venv
source .venv/bin/activate      # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

Then open **http://127.0.0.1:8000** in a browser.

## Project layout

```
app/
  main.py        FastAPI app: API routes + serves the frontend
  tracking.py     Skyfield orbital-mechanics calculations (passes, ground track)
  satellites.py   Preset satellites + their TLEs (ISS, NOAA 20, NOAA 15)
  stations.py     Preset ground stations (Bangalore, Hyderabad, Chennai)
static/
  index.html      Dashboard page
  app.js          Fetches data from the API, draws the map, runs mock telemetry
  style.css       Styling
```

## Key concepts, briefly

- **TLE (Two-Line Element set)**: a compact two-line text format that
  encodes a satellite's orbit at a specific reference time — its shape,
  tilt, and where the satellite was. Feed a TLE into an orbit-propagation
  model (SGP4, which Skyfield uses internally) and you can calculate
  where the satellite is at any past or future time. TLEs drift out of
  date after roughly one to two weeks because atmospheric drag and small
  maneuvers aren't in the model, so real systems refresh them regularly
  from a source like Celestrak. The three bundled here were fetched fresh
  for this demo — if it's been more than ~2 weeks, pull new ones from
  https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=TLE
  (swap the CATNR for NOAA 20 = 43013, NOAA 15 = 25338) and paste them
  into `app/satellites.py`.

- **Pass**: the window during which a satellite is above the horizon for
  a given ground station and could plausibly be tracked or contacted.
  Each pass has a rise time (crosses the horizon coming into view), a
  culmination (highest point reached), and a set time (drops back below
  the horizon).

- **Elevation**: how high the satellite is above the horizon, in
  degrees — 0° is right at the horizon, 90° is directly overhead. Passes
  with low max elevation are usually poor for communication (more
  atmosphere and obstructions in the way); this demo only shows passes
  that climb above 10°.

- **Ground track**: the path traced on Earth's surface directly beneath
  the satellite as it orbits. It's what's drawn as the blue line on the
  map.

## Extending this further

If the idea is worth pursuing, natural next steps: refresh TLEs
automatically from Celestrak's API instead of hardcoding them, let users
paste in an arbitrary TLE/ground-station pair instead of picking from
presets, and replace the fake telemetry with data from an actual
radio/SDR feed during a real pass.
