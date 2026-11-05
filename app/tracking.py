"""
Orbital-mechanics calculations, powered by Skyfield.

Skyfield takes a TLE (see satellites.py) and, using the same SGP4 physics
model that real ground stations use, tells you exactly where a satellite
is at any point in time and whether a given point on Earth can "see" it.

Two things this module computes:

1. PASSES — the windows of time a satellite is above the horizon for a
   ground station. A "pass" has:
     - rise time   : the moment the satellite crosses the horizon, coming
                      into view
     - culmination : the moment it reaches its highest point in the sky
                      during that pass (max elevation)
     - set time    : the moment it drops back below the horizon
     - max elevation: how high above the horizon it gets, in degrees.
                      0 deg = right at the horizon, 90 deg = directly
                      overhead. Higher elevation generally means a
                      stronger, cleaner radio link.
     - duration    : set time minus rise time — how long the ground
                      station has to talk to the satellite.

2. GROUND TRACK — the path the satellite's sub-point (the spot on Earth
   directly below it) traces out over time, so it can be drawn as a line
   on a map.
"""

from datetime import timedelta

from skyfield.api import EarthSatellite, load, wgs84

# Skyfield's timescale object handles conversions between UTC, TT, etc.
# It downloads/uses a small almanac file the first time it runs.
_ts = load.timescale()

# Elevation cutoff: below ~10 degrees, buildings/trees/atmosphere usually
# block or badly degrade the signal, so most ground stations ignore passes
# that never climb higher than this.
MIN_USABLE_ELEVATION_DEG = 10.0


def _build_satellite(tle_lines, name):
    return EarthSatellite(tle_lines[0], tle_lines[1], name, _ts)


def predict_passes(tle_lines, sat_name, lat, lon, elevation_m, days=7):
    """Return upcoming passes over the next `days` days for one ground station."""
    satellite = _build_satellite(tle_lines, sat_name)
    station = wgs84.latlon(lat, lon, elevation_m=elevation_m)

    now = _ts.now()
    end = _ts.from_datetime(now.utc_datetime() + timedelta(days=days))

    # find_events scans the time window and returns every rise/culminate/set
    # moment where the satellite crosses MIN_USABLE_ELEVATION_DEG.
    times, events = satellite.find_events(
        station, now, end, altitude_degrees=MIN_USABLE_ELEVATION_DEG
    )

    passes = []
    current = {}
    for t, event in zip(times, events):
        if event == 0:  # rise
            current = {"rise": t}
        elif event == 1 and "rise" in current:  # culminate (peak elevation)
            alt, az, distance = (satellite - station).at(t).altaz()
            current["culminate"] = t
            current["max_elevation_deg"] = round(alt.degrees, 1)
            current["azimuth_at_max_deg"] = round(az.degrees, 1)
            current["range_at_max_km"] = round(distance.km, 1)
        elif event == 2 and "rise" in current:  # set
            current["set"] = t
            if "culminate" in current:
                rise_dt = current["rise"].utc_datetime()
                set_dt = current["set"].utc_datetime()
                passes.append(
                    {
                        "rise_time": rise_dt.isoformat(),
                        "culmination_time": current["culminate"].utc_datetime().isoformat(),
                        "set_time": set_dt.isoformat(),
                        "duration_seconds": round((set_dt - rise_dt).total_seconds()),
                        "max_elevation_deg": current["max_elevation_deg"],
                        "azimuth_at_max_deg": current["azimuth_at_max_deg"],
                        "range_at_max_km": current["range_at_max_km"],
                    }
                )
            current = {}

    return passes


def ground_track(tle_lines, sat_name, minutes=110, step_seconds=30):
    """
    Sample the satellite's sub-point (lat/lon on Earth directly below it)
    every `step_seconds` for the next `minutes` minutes, so the frontend
    can draw it as a line on a map. ~110 minutes covers roughly one full
    orbit for a low-Earth-orbit satellite like the ISS.
    """
    satellite = _build_satellite(tle_lines, sat_name)
    now = _ts.now()
    now_dt = now.utc_datetime()

    points = []
    steps = int((minutes * 60) / step_seconds)
    for i in range(steps + 1):
        t = _ts.from_datetime(now_dt + timedelta(seconds=i * step_seconds))
        subpoint = satellite.at(t).subpoint()
        points.append(
            {
                "lat": round(subpoint.latitude.degrees, 4),
                "lon": round(subpoint.longitude.degrees, 4),
                "time": t.utc_datetime().isoformat(),
            }
        )
    return points


def current_position(tle_lines, sat_name):
    """Where is the satellite right now? Used to place a live marker on the map."""
    satellite = _build_satellite(tle_lines, sat_name)
    t = _ts.now()
    subpoint = satellite.at(t).subpoint()
    return {
        "lat": round(subpoint.latitude.degrees, 4),
        "lon": round(subpoint.longitude.degrees, 4),
        "altitude_km": round(subpoint.elevation.km, 1),
        "time": t.utc_datetime().isoformat(),
    }
