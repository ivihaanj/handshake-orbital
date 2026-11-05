# Preset satellites for the demo.
#
# A TLE ("Two-Line Element set") is a compact text format that encodes a
# satellite's orbit: its shape, tilt, and where it was at a specific
# reference time. Given a TLE, orbital-mechanics software (here, Skyfield)
# can calculate where the satellite will be at any past or future moment.
#
# TLEs go stale after a couple of weeks because atmospheric drag and small
# maneuvers shift the real orbit away from the model. These three were
# pulled fresh from Celestrak (https://celestrak.org) for this demo. For a
# real tool you'd refresh them periodically from Celestrak's API.

SATELLITES = {
    "iss": {
        "name": "ISS (ZARYA)",
        "description": "International Space Station — low orbit, visible often, easy to spot.",
        "tle": [
            "1 25544U 98067A   26199.86307315  .00004074  00000+0  81939-4 0  9998",
            "2 25544  51.6317 143.3357 0006807 311.9483  48.0925 15.49045026576665",
        ],
    },
    "noaa20": {
        "name": "NOAA 20 (JPSS-1)",
        "description": "Polar-orbiting weather satellite, sun-synchronous orbit.",
        "tle": [
            "1 43013U 17073A   26199.93160338  .00000031  00000+0  35547-4 0  9990",
            "2 43013  98.7772 139.1131 0001524 120.4647 239.6680 14.19516914448975",
        ],
    },
    "noaa15": {
        "name": "NOAA 15",
        "description": "Older polar-orbiting weather satellite, still active.",
        "tle": [
            "1 25338U 98030A   26199.94542278  .00000029  00000+0  29584-4 0  9991",
            "2 25338  98.5064 219.7195 0009060 252.2814 107.7378 14.27155029465822",
        ],
    },
}
