#!/usr/bin/env python3
"""Generate the vATIS profile for Uzbekistan (UZTT / UZSS / UZFF / UZNN).

The ATIS format block (metric visibility, QNH in hPa) is taken from the UNNT
reference profile, since Uzbekistan uses the same ICAO/CIS-style ATIS
phraseology. Two blocks are overridden:

- surface wind is reported in knots, not metres per second;
- since 2 October 2025 Uzbekistan uses a unified transition altitude of
  13000 ft with a fixed transition level of FL150, replacing the metric,
  QNH-dependent transition level table of the reference profile.

The same 2 October 2025 change replaced the Soviet-era UT location indicator
prefix with UZ (the former UTTT becoming UZTT and so on, last two letters
retained). Stations use the new UZ identifiers; the legacy UT code is recorded
per airport as `legacy_icao` for reference only.

The ATIS text is laid out one element per line rather than as a single
paragraph, so the individual weather variables are used instead of
[FULL_WX_STRING].
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


# The report is rendered one element per line, so each line has to name what it
# is. The reference profile's METAR-style text fragments (T16, QNH1006) are
# replaced with spelled-out text matching how the element is spoken.
TEXT_TEMPLATE_OVERRIDES = {
    "observationTime": "{time}Z",
    "visibility": "VIS {visibility}",
    "temperature": "TEMPERATURE {temp}",
    "dewpoint": "DEWPOINT {dewpoint}",
    "altimeter": "QNH {altimeter} HPA",
}


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


# identifier, city name, spoken facility name, ATIS frequency (Hz), magnetic
# variation (negative = East), runways and the controller positions that work
# the field.
#
# Tashkent data is taken from AIP Uzbekistan, UZTT AD 2.24-1.0 / 1.0-1
# (Aerodrome Chart - ICAO, AIRAC AMDT 03/26, 14 MAY 26): declared distances,
# the taxiway table and the ATS frequency box. "tora" is the full-length TORA
# from the threshold; "intersections" are the published intersection-departure
# TORAs, in the order the chart lists them.
#
# The other three aerodromes have no chart on file, so their runway lengths are
# from open sources and no declared distances are published for them.
AIRPORTS = [
    {
        "identifier": "UZTT",
        "legacy_icao": "UTTT",
        "name": "Tashkent",
        "spoken": "TASHKENT ISLAM KARIMOV",
        # AIP: ATIS 126.8.
        "frequency": 126800000,
        # AIP: VAR 5 degrees 38 minutes E (2025).
        "magvar": -6,
        "positions": [
            "UZTT_DEL",
            "UZTT_GND",
            "UZTT_TWR",
            "UZTT_APP",
            "UZTR_CTR",
            "RU-CEN_FSS",
        ],
        "runways": [
            # 08L/26R: HIALS CAT II / CAT I. 08R: HIALS CAT I. 26L has MIALS
            # 420 m only, so it is flown as a non-precision approach.
            {"rwy": "08L", "app": "ILS", "length": 4000, "tora": 4000,
             "intersections": [("TWY 2", 3460), ("TWY 3", 2425)]},
            {"rwy": "26R", "app": "ILS", "length": 4000, "tora": 4000,
             "intersections": [("TWY 4", 2725), ("TWY 3", 1200)]},
            {"rwy": "08R", "app": "ILS", "length": 3905, "tora": 3755,
             "intersections": [("TWY 12", 3075), ("TWY 8", 2520),
                               ("TWY 13", 2100)]},
            {"rwy": "26L", "app": "RNP", "length": 3905, "tora": 3905,
             "intersections": [("TWY 14", 2350), ("TWY 13", 1300)]},
        ],
        # Parallel-runway combinations that are actually usable at Tashkent.
        "combos": [("08L", "08R"), ("26R", "26L")],
        # AIP note on the chart.
        "note": "DEPARTING ACFT CTC [UZTT_DEL] FOR ATC CLEARANCE "
                "NOT EARLIER THAN 15 MIN BEFORE START-UP.",
    },
    {
        "identifier": "UZSS",
        "legacy_icao": "UTSS",
        "name": "Samarkand",
        "spoken": "SAMARKAND",
        "frequency": 127200000,
        "magvar": -5,
        # No dedicated Samarkand positions are published; worked top-down.
        "positions": ["UZTR_CTR", "RU-CEN_FSS"],
        "runways": [
            {"rwy": "09", "app": "ILS", "length": 3100},
            {"rwy": "27", "app": "RNP", "length": 3100},
        ],
        "combos": [],
    },
    {
        "identifier": "UZFF",
        "legacy_icao": "UTFF",
        "name": "Fergana",
        "spoken": "FERGANA",
        "frequency": 127400000,
        "magvar": -5,
        # No dedicated Fergana positions are published; worked top-down.
        "positions": ["UZTR_CTR", "RU-CEN_FSS"],
        "runways": [
            {"rwy": "08", "app": "RNP", "length": 2700},
            {"rwy": "26", "app": "ILS", "length": 2700},
        ],
        "combos": [],
    },
    {
        "identifier": "UZNN",
        "legacy_icao": "UTNN",
        "name": "Namangan",
        "spoken": "NAMANGAN",
        "frequency": 127600000,
        "magvar": -5,
        # No dedicated Namangan positions are published; worked top-down.
        "positions": ["UZTR_CTR", "RU-CEN_FSS"],
        "runways": [
            {"rwy": "08", "app": "RNP", "length": 3000},
            {"rwy": "26", "app": "RNP", "length": 3000},
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
            "text": "WIND {wind_dir} DEGREES {wind_spd} KT",
            "voice": "WIND {wind_dir} DEGREES {wind_spd} KNOTS..",
        }
    },
    "standardGust": {
        "template": {
            "text": "WIND {wind_dir} DEGREES {wind_spd} GUSTS {wind_gust} KT",
            "voice": "WIND {wind_dir} DEGREES {wind_spd} GUSTS {wind_gust} KNOTS..",
        }
    },
    "variable": {
        "template": {
            "text": "WIND VARIABLE {wind_spd} KT",
            "voice": "WIND VARIABLE {wind_spd} KNOTS..",
        }
    },
    "variableGust": {
        "template": {
            "text": "WIND VARIABLE {wind_spd} GUSTS {wind_gust} KT",
            "voice": "WIND VARIABLE {wind_spd} GUSTS {wind_gust} KNOTS..",
        }
    },
    "variableDirection": {
        "template": {
            "text": "WIND VARIABLE BETWEEN {wind_vmin} AND {wind_vmax}",
            "voice": "WIND VARIABLE BETWEEN {wind_vmin} AND {wind_vmax}..",
        }
    },
    "calm": {
        "calmWindSpeed": 0,
        "template": {"text": "WIND CALM", "voice": "WIND CALM.."},
    },
}

# Unified since 2 October 2025: transition altitude 13000 ft, transition level
# FL150 regardless of QNH (previously 6000 ft / FL080).
TRANSITION_LEVEL_FIXED = {
    "values": [{"low": 0, "high": 1099, "altitude": 150}],
    "template": {
        "text": "TRANSITION LEVEL {trl}",
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


def template(spoken, arr, dep, note=None):
    """One ATIS element per line.

    [FULL_WX_STRING] would collapse the whole observation onto a single line,
    so the individual weather variables are spelled out instead. Visibility and
    present weather share a line: present weather is empty in fair conditions
    and would otherwise leave a blank line in the middle of the report.
    """
    lines = [
        f"{spoken} ATIS INFO [ATIS_CODE]. [OBS_TIME].",
        f"RWY {arr['rwy']}. EXPECT {arr['app']} APPROACH.",
        f"DEP RWY {dep['rwy']}.",
        "[TL].",
        "[WIND].",
        "[VIS] [PRESENT_WX]",
        "[CLOUDS]",
        "[TEMP]. [DEW].",
        "[PRESSURE].",
    ]
    if dep.get("tora"):
        lines.append(f"TORA RWY {dep['rwy']} {dep['tora']} M.")
    if dep.get("intersections"):
        parts = ", ".join(f"FROM {twy} {tora} M" for twy, tora in dep["intersections"])
        lines.append(f"INTERSECTION DEPARTURE TORA {parts}.")
    if note:
        lines.append(note)
    lines.append("ON INITIAL CTC REPORT STAND AND READINESS.")
    # Trailing newline: vATIS appends the closing statement directly to the
    # template, which would otherwise run into the last line.
    return "\n".join(lines) + "\n"


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
                "template": template(airport["spoken"], rwy, rwy, airport.get("note")),
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
                "template": template(
                    airport["spoken"], by_rwy[arr], by_rwy[dep],
                    airport.get("note"),
                ),
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
    for element, text in TEXT_TEMPLATE_OVERRIDES.items():
        fmt[element]["template"]["text"] = text
    # Inherited stray dots that would show up mid-line in a column layout.
    fmt["dewpoint"]["template"]["text"] = fmt["dewpoint"]["template"]["text"].rstrip(".")
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
