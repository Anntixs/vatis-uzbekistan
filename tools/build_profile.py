#!/usr/bin/env python3
"""Generate the vATIS profile for Uzbekistan (UTTT / UTSS / UTFF / UTNN).

The ATIS format block (metric visibility, QNH in hPa) is taken from the UNNT
reference profile, since Uzbekistan uses the same ICAO/CIS-style ATIS
phraseology. Two blocks are overridden:

- surface wind is reported in knots, not metres per second;
- since 2 October 2025 Uzbekistan uses a unified transition altitude of
  13000 ft with a fixed transition level of FL150, replacing the metric,
  QNH-dependent transition level table of the reference profile.

The same 2 October 2025 change replaced the Soviet-era UT location indicator
prefix with UZ (the former UTTT becoming UZTT and so on, last two letters
retained). vATIS does not recognise the UZ identifiers yet, so stations keep
their legacy UT identifiers -- that is the code vATIS looks the aerodrome up
by. The new code is recorded per airport as `icao` for reference only. VATSIM
controller callsigns are unaffected by this and use the UZ form.
"""

import copy
import json
import sys
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REFERENCE = REPO / "reference" / "vATIS_Profile_UNNT.json"
OUTPUT = REPO / "profiles" / "vATIS_Profile_Uzbekistan.json"

# Deterministic ids so regenerating the profile does not churn the diff.
NS = uuid.UUID("6f1f6d5c-0a3c-5f4e-9b7a-2f0b7c1d4e55")


def det_id(*parts):
    return str(uuid.uuid5(NS, "/".join(parts)))


COMMON_CONTRACTIONS = [
    ("INFO", "INFO", "INFORMATION"),
    ("Z", "Z", "ZULU"),
    ("APP", "APP", "APPROACH"),
    ("APPS", "APPS", "APPROACHES"),
    ("ARR", "ARR", "ARRIVAL"),
    ("DEP", "DEP", "DEPARTURE"),
    ("RWY", "RWY", "RUNWAY"),
    ("TWY", "TWY", "TAXIWAY"),
    ("FREQ", "FREQ", "FREQUENCY"),
    ("CTC", "CTC", "CONTACT"),
    ("VIS", "VIS", "VISIBILITY"),
    ("M", "M", "METRES"),
    ("TORA", "TORA", "TAKEOFF RUN AVAILABLE"),
    ("A", "A", "ALPHA"),
    ("B", "B", "BRAVO"),
    ("C", "C", "CHARLIE"),
    ("D", "D", "DELTA"),
    ("E", "E", "ECHO"),
]

# VATSIM (VATRUS / Central Asian Zone) controller positions, as published on
# 8 September 2026. Only UZTT has dedicated aerodrome positions; the Fergana
# Valley and Samarkand fields are worked top-down from Tashkent Control or from
# the Central Asian Zone FSS.
#   logon callsign, spoken name, frequency in MHz
ATC_POSITIONS = {
    "UZTT_DEL": ("TASHKENT DELIVERY", "129.400"),
    "UZTT_GND": ("TASHKENT GROUND", "121.700"),
    "UZTT_TWR": ("TASHKENT TOWER", "120.400"),
    "UZTT_APP": ("TASHKENT APPROACH", "119.400"),
    "UZTR_CTR": ("TASHKENT CONTROL", "134.600"),
    "RU-CEN_FSS": ("ASIA CENTER", "132.850"),
}


def position(callsign):
    """Contraction row for a controller position: text is the logon callsign."""
    spoken, freq = ATC_POSITIONS[callsign]
    return (callsign.replace("-", "_"), callsign, f"{spoken} ON {freq}")


# identifier, city name, spoken facility name, ATIS frequency (Hz),
# magnetic variation (negative = East), taxiway/TORA data per runway,
# and the controller positions that work the field.
AIRPORTS = [
    {
        # vATIS still requires the legacy identifier; new code: UZTT.
        "identifier": "UTTT",
        "icao": "UZTT",
        "name": "Tashkent",
        "spoken": "TASHKENT ISLAM KARIMOV",
        "frequency": 127000000,
        "magvar": -5,
        "positions": [
            "UZTT_DEL",
            "UZTT_GND",
            "UZTT_TWR",
            "UZTT_APP",
            "UZTR_CTR",
            "RU-CEN_FSS",
        ],
        "runways": [
            {"rwy": "08L", "app": "ILS", "twy": "A", "tora": 4000},
            {"rwy": "26R", "app": "ILS", "twy": "D", "tora": 4000},
            {"rwy": "08R", "app": "RNP", "twy": "B", "tora": 3800},
            {"rwy": "26L", "app": "RNP", "twy": "E", "tora": 3800},
        ],
        # Parallel-runway combinations that are actually usable at Tashkent.
        "combos": [("08L", "08R"), ("26R", "26L")],
    },
    {
        # vATIS still requires the legacy identifier; new code: UZSS.
        "identifier": "UTSS",
        "icao": "UZSS",
        "name": "Samarkand",
        "spoken": "SAMARKAND",
        "frequency": 127200000,
        "magvar": -5,
        # No dedicated Samarkand positions are published; worked top-down.
        "positions": ["UZTR_CTR", "RU-CEN_FSS"],
        "runways": [
            {"rwy": "09", "app": "ILS", "twy": "A", "tora": 3100},
            {"rwy": "27", "app": "RNP", "twy": "C", "tora": 3100},
        ],
        "combos": [],
    },
    {
        # vATIS still requires the legacy identifier; new code: UZFF.
        "identifier": "UTFF",
        "icao": "UZFF",
        "name": "Fergana",
        "spoken": "FERGANA",
        "frequency": 127400000,
        "magvar": -5,
        # No dedicated Fergana positions are published; worked top-down.
        "positions": ["UZTR_CTR", "RU-CEN_FSS"],
        "runways": [
            {"rwy": "08", "app": "RNP", "twy": "A", "tora": 2700},
            {"rwy": "26", "app": "ILS", "twy": "B", "tora": 2700},
        ],
        "combos": [],
    },
    {
        # vATIS still requires the legacy identifier; new code: UZNN.
        "identifier": "UTNN",
        "icao": "UZNN",
        "name": "Namangan",
        "spoken": "NAMANGAN",
        "frequency": 127600000,
        "magvar": -5,
        # No dedicated Namangan positions are published; worked top-down.
        "positions": ["UZTR_CTR", "RU-CEN_FSS"],
        "runways": [
            {"rwy": "08", "app": "RNP", "twy": "A", "tora": 3000},
            {"rwy": "26", "app": "RNP", "twy": "B", "tora": 3000},
        ],
        "combos": [],
    },
]

# Uzbekistan reports surface wind in knots, so the MPS templates inherited from
# the reference profile are replaced wholesale.
SURFACE_WIND_KNOTS = {
    "speakLeadingZero": False,
    "standard": {
        "template": {
            "text": "{wind_dir}{wind_spd}KT",
            "voice": "WIND {wind_dir} DEGREES {wind_spd} KNOTS..",
        }
    },
    "standardGust": {
        "template": {
            "text": "{wind_dir}{wind_spd}G{wind_gust}KT",
            "voice": "WIND {wind_dir} DEGREES {wind_spd} GUSTS {wind_gust} KNOTS..",
        }
    },
    "variable": {
        "template": {
            "text": "VRB{wind_spd}KT",
            "voice": "WIND VARIABLE {wind_spd} KNOTS..",
        }
    },
    "variableGust": {
        "template": {
            "text": "VRB{wind_spd}G{wind_gust}KT",
            "voice": "WIND VARIABLE {wind_spd} GUSTS {wind_gust} KNOTS..",
        }
    },
    "variableDirection": {
        "template": {
            "text": "{wind_vmin}V{wind_vmax}",
            "voice": "WIND VARIABLE BETWEEN {wind_vmin} AND {wind_vmax}..",
        }
    },
    "calm": {
        "calmWindSpeed": 0,
        "template": {"text": "{wind}", "voice": "WIND CALM.."},
    },
}

# Unified since 2 October 2025: transition altitude 13000 ft, transition level
# FL150 regardless of QNH (previously 6000 ft / FL080).
TRANSITION_LEVEL_FIXED = {
    "values": [{"low": 0, "high": 1099, "altitude": 150}],
    "template": {
        "text": "TL{trl}",
        "voice": "TRANSITION LEVEL {trl}..",
    },
}

EXT_GENERATOR = {
    "enabled": False,
    "textUrl": "",
    "voiceUrl": "",
    "arrival": "",
    "departure": "",
    "approaches": "",
    "remarks": "",
}


def contractions(airport):
    rows = COMMON_CONTRACTIONS + [position(c) for c in airport["positions"]]
    return [{"variableName": v, "text": t, "voice": s} for v, t, s in rows]


def template(spoken, arr, dep):
    return (
        f"{spoken} ATIS INFO [ATIS_CODE].. [OBS_TIME].. "
        f"EXPECT {arr['app']} APP RWY {arr['rwy']}.. DEP RWY {dep['rwy']}.. "
        f"[FULL_WX_STRING].. [TL].. "
        f"TORA FROM TWY {dep['twy']} {dep['tora']} M.. "
        f"ON INITIAL CTC REPORT STAND AND READINESS.."
    )


def presets(airport):
    by_rwy = {r["rwy"]: r for r in airport["runways"]}
    out = []
    for rwy in airport["runways"]:
        out.append(
            {
                "id": det_id(airport["identifier"], "preset", rwy["rwy"]),
                "name": rwy["rwy"],
                "airportConditions": "",
                "notams": "",
                "template": template(airport["spoken"], rwy, rwy),
                "externalGenerator": copy.deepcopy(EXT_GENERATOR),
            }
        )
    for arr, dep in airport["combos"]:
        name = f"{arr}+{dep}"
        out.append(
            {
                "id": det_id(airport["identifier"], "preset", name),
                "name": name,
                "airportConditions": "",
                "notams": "",
                "template": template(airport["spoken"], by_rwy[arr], by_rwy[dep]),
                "externalGenerator": copy.deepcopy(EXT_GENERATOR),
            }
        )
    return out


def build_station(airport, atis_format):
    fmt = copy.deepcopy(atis_format)
    fmt["surfaceWind"] = copy.deepcopy(SURFACE_WIND_KNOTS)
    fmt["surfaceWind"]["magneticVariation"] = {
        "enabled": True,
        "magneticDegrees": airport["magvar"],
    }
    fmt["transitionLevel"] = copy.deepcopy(TRANSITION_LEVEL_FIXED)
    return {
        "id": det_id(airport["identifier"], "station"),
        "ordinal": 0,
        "identifier": airport["identifier"],
        "name": airport["name"],
        "atisType": "Combined",
        "codeRange": {"low": "A", "high": "Z"},
        "atisFormat": fmt,
        "notamsBeforeFreeText": False,
        "airportConditionsBeforeFreeText": False,
        "frequency": airport["frequency"],
        "idsEndpoint": "",
        "useDecimalTerminology": True,
        "atisVoice": {
            "useTextToSpeech": True,
            "voice": "UK Female",
            "speechRate": 150,
        },
        "presets": presets(airport),
        "contractions": contractions(airport),
        "airportConditionDefinitions": [],
        "notamDefinitions": [],
    }


def main():
    if not REFERENCE.exists():
        sys.exit(f"reference profile not found: {REFERENCE}")
    reference = json.loads(REFERENCE.read_text(encoding="utf-8"))
    base = next(s for s in reference["stations"] if s["identifier"] == "UNBB")
    atis_format = base["atisFormat"]

    profile = {
        "name": "Uzbekistan",
        "id": det_id("profile", "uzbekistan"),
        "stations": [build_station(a, atis_format) for a in AIRPORTS],
        "version": reference["version"],
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(profile, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote {OUTPUT} ({OUTPUT.stat().st_size} bytes)")
    for s in profile["stations"]:
        print(f"  {s['identifier']} {s['name']:<10} {s['frequency']/1e6:.3f} MHz  "
              f"{len(s['presets'])} presets")


if __name__ == "__main__":
    main()
