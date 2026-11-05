"""
FastAPI backend for the ground-station dashboard prototype.

Endpoints:
  GET /api/satellites       -> the preset satellites the dropdown offers
  GET /api/ground-stations   -> the preset ground stations the dropdown offers
  GET /api/passes            -> upcoming passes for a satellite+station pair
  GET /api/ground-track      -> points to draw the satellite's path on a map
  GET /api/current-position  -> where the satellite is right now

The mock telemetry panel (battery/temperature/signal) is intentionally
generated in the browser (see static/app.js) rather than here — it's fake
data meant only to preview the UI, so there's no need for a backend
round-trip to produce it.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from .satellites import SATELLITES
from .stations import GROUND_STATIONS
from .tracking import current_position, ground_track, predict_passes

app = FastAPI(title="Ground Station Dashboard (prototype)")


def _get_satellite_or_404(satellite_id: str):
    sat = SATELLITES.get(satellite_id)
    if not sat:
        raise HTTPException(status_code=404, detail=f"Unknown satellite '{satellite_id}'")
    return sat


def _get_station_or_404(station_id: str):
    station = GROUND_STATIONS.get(station_id)
    if not station:
        raise HTTPException(status_code=404, detail=f"Unknown ground station '{station_id}'")
    return station


@app.get("/api/satellites")
def list_satellites():
    return [
        {"id": sat_id, "name": sat["name"], "description": sat["description"]}
        for sat_id, sat in SATELLITES.items()
    ]


@app.get("/api/ground-stations")
def list_ground_stations():
    return [
        {"id": station_id, "name": s["name"], "lat": s["lat"], "lon": s["lon"]}
        for station_id, s in GROUND_STATIONS.items()
    ]


@app.get("/api/passes")
def get_passes(satellite: str, station: str, days: int = 7):
    sat = _get_satellite_or_404(satellite)
    st = _get_station_or_404(station)
    days = max(1, min(days, 14))  # keep the demo from being asked to crunch huge windows

    passes = predict_passes(
        sat["tle"], sat["name"], st["lat"], st["lon"], st["elevation_m"], days=days
    )
    return {
        "satellite": sat["name"],
        "ground_station": st["name"],
        "days": days,
        "min_usable_elevation_deg": 10.0,
        "passes": passes,
    }


@app.get("/api/ground-track")
def get_ground_track(satellite: str, minutes: int = 110):
    sat = _get_satellite_or_404(satellite)
    minutes = max(10, min(minutes, 240))
    return {
        "satellite": sat["name"],
        "points": ground_track(sat["tle"], sat["name"], minutes=minutes),
    }


@app.get("/api/current-position")
def get_current_position(satellite: str):
    sat = _get_satellite_or_404(satellite)
    return {"satellite": sat["name"], **current_position(sat["tle"], sat["name"])}


# Serve the frontend last so it doesn't shadow the /api routes above.
app.mount("/", StaticFiles(directory="static", html=True), name="static")
