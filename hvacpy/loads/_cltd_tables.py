"""CLTD and CLF lookup tables — ASHRAE 1997 HOF Chapter 28.

Data only — dicts and lookup functions. No imports from other hvacpy modules.
All values are exact transcriptions from the specification.
"""

from __future__ import annotations

from hvacpy.exceptions import DesignConditionsNotFoundError

# ── Wall Group Descriptions ─────────────────────────────────────────

WALL_GROUP_DESCRIPTIONS: dict[str, str] = {
    'A': 'Curtain wall or spandrel — very lightweight. Mass < 50 kg/m². e.g. metal panels.',
    'B': 'Light frame — wood or metal stud with insulation board. Mass 50–100 kg/m².',
    'C': 'Light masonry — 100mm brick or concrete block, insulated. Mass 100–200 kg/m².',
    'D': 'Medium masonry — 200mm brick, cavity wall, or concrete. Mass 200–400 kg/m². Default.',
    'E': 'Heavy masonry — 300mm brick or 200mm concrete. Mass 400–600 kg/m².',
    'F': 'Very heavy — 300mm+ concrete. Mass > 600 kg/m².',
    'G': 'Roofs — flat or low-slope roofs with insulation. Use for is_roof=True surfaces.',
}


# ── CLTD Table — Group D Walls and Roofs ────────────────────────────
# Values are °C at base conditions: T_outdoor=35°C, T_indoor=24°C,
# latitude 32°N, July 21.
# Keys: (hour_24, orientation_str)
# Hour 1 = 01:00, Hour 24 = 24:00 (midnight)

CLTD_GROUP_D: dict[tuple[int, str], float] = {
    # Hour 01
    (1, 'N'): 1, (1, 'NE'): 1, (1, 'E'): 1, (1, 'SE'): 1,
    (1, 'S'): 1, (1, 'SW'): 2, (1, 'W'): 2, (1, 'NW'): 1, (1, 'H'): 3,
    # Hour 02
    (2, 'N'): 0, (2, 'NE'): 0, (2, 'E'): 1, (2, 'SE'): 0,
    (2, 'S'): 0, (2, 'SW'): 1, (2, 'W'): 1, (2, 'NW'): 1, (2, 'H'): 2,
    # Hour 03
    (3, 'N'): 0, (3, 'NE'): 0, (3, 'E'): 0, (3, 'SE'): 0,
    (3, 'S'): 0, (3, 'SW'): 1, (3, 'W'): 1, (3, 'NW'): 0, (3, 'H'): 1,
    # Hour 04
    (4, 'N'): -1, (4, 'NE'): -1, (4, 'E'): 0, (4, 'SE'): -1,
    (4, 'S'): -1, (4, 'SW'): 0, (4, 'W'): 0, (4, 'NW'): 0, (4, 'H'): 1,
    # Hour 05
    (5, 'N'): -1, (5, 'NE'): -1, (5, 'E'): -1, (5, 'SE'): -1,
    (5, 'S'): -1, (5, 'SW'): 0, (5, 'W'): 0, (5, 'NW'): -1, (5, 'H'): 0,
    # Hour 06
    (6, 'N'): -1, (6, 'NE'): -1, (6, 'E'): -1, (6, 'SE'): -1,
    (6, 'S'): -1, (6, 'SW'): 0, (6, 'W'): 0, (6, 'NW'): -1, (6, 'H'): 0,
    # Hour 07
    (7, 'N'): 0, (7, 'NE'): 1, (7, 'E'): 2, (7, 'SE'): 1,
    (7, 'S'): 0, (7, 'SW'): 0, (7, 'W'): 0, (7, 'NW'): 0, (7, 'H'): 1,
    # Hour 08
    (8, 'N'): 1, (8, 'NE'): 3, (8, 'E'): 6, (8, 'SE'): 4,
    (8, 'S'): 1, (8, 'SW'): 1, (8, 'W'): 1, (8, 'NW'): 1, (8, 'H'): 4,
    # Hour 09
    (9, 'N'): 2, (9, 'NE'): 5, (9, 'E'): 10, (9, 'SE'): 7,
    (9, 'S'): 2, (9, 'SW'): 1, (9, 'W'): 1, (9, 'NW'): 1, (9, 'H'): 9,
    # Hour 10
    (10, 'N'): 3, (10, 'NE'): 6, (10, 'E'): 13, (10, 'SE'): 10,
    (10, 'S'): 4, (10, 'SW'): 2, (10, 'W'): 2, (10, 'NW'): 2, (10, 'H'): 15,
    # Hour 11
    (11, 'N'): 5, (11, 'NE'): 7, (11, 'E'): 14, (11, 'SE'): 12,
    (11, 'S'): 6, (11, 'SW'): 3, (11, 'W'): 3, (11, 'NW'): 2, (11, 'H'): 21,
    # Hour 12
    (12, 'N'): 6, (12, 'NE'): 7, (12, 'E'): 13, (12, 'SE'): 12,
    (12, 'S'): 8, (12, 'SW'): 4, (12, 'W'): 3, (12, 'NW'): 3, (12, 'H'): 27,
    # Hour 13
    (13, 'N'): 8, (13, 'NE'): 8, (13, 'E'): 12, (13, 'SE'): 12,
    (13, 'S'): 9, (13, 'SW'): 6, (13, 'W'): 4, (13, 'NW'): 4, (13, 'H'): 32,
    # Hour 14
    (14, 'N'): 10, (14, 'NE'): 8, (14, 'E'): 11, (14, 'SE'): 11,
    (14, 'S'): 10, (14, 'SW'): 8, (14, 'W'): 6, (14, 'NW'): 5, (14, 'H'): 35,
    # Hour 15
    (15, 'N'): 11, (15, 'NE'): 9, (15, 'E'): 10, (15, 'SE'): 10,
    (15, 'S'): 10, (15, 'SW'): 10, (15, 'W'): 8, (15, 'NW'): 6, (15, 'H'): 37,
    # Hour 16
    (16, 'N'): 12, (16, 'NE'): 9, (16, 'E'): 9, (16, 'SE'): 9,
    (16, 'S'): 10, (16, 'SW'): 12, (16, 'W'): 11, (16, 'NW'): 8, (16, 'H'): 36,
    # Hour 17
    (17, 'N'): 13, (17, 'NE'): 10, (17, 'E'): 9, (17, 'SE'): 9,
    (17, 'S'): 9, (17, 'SW'): 13, (17, 'W'): 13, (17, 'NW'): 10, (17, 'H'): 33,
    # Hour 18
    (18, 'N'): 13, (18, 'NE'): 10, (18, 'E'): 8, (18, 'SE'): 8,
    (18, 'S'): 8, (18, 'SW'): 13, (18, 'W'): 15, (18, 'NW'): 12, (18, 'H'): 28,
    # Hour 19
    (19, 'N'): 12, (19, 'NE'): 10, (19, 'E'): 8, (19, 'SE'): 8,
    (19, 'S'): 7, (19, 'SW'): 13, (19, 'W'): 15, (19, 'NW'): 13, (19, 'H'): 22,
    # Hour 20
    (20, 'N'): 11, (20, 'NE'): 9, (20, 'E'): 8, (20, 'SE'): 7,
    (20, 'S'): 6, (20, 'SW'): 12, (20, 'W'): 14, (20, 'NW'): 13, (20, 'H'): 16,
    # Hour 21
    (21, 'N'): 9, (21, 'NE'): 8, (21, 'E'): 7, (21, 'SE'): 6,
    (21, 'S'): 5, (21, 'SW'): 10, (21, 'W'): 13, (21, 'NW'): 12, (21, 'H'): 11,
    # Hour 22
    (22, 'N'): 7, (22, 'NE'): 6, (22, 'E'): 6, (22, 'SE'): 5,
    (22, 'S'): 4, (22, 'SW'): 8, (22, 'W'): 10, (22, 'NW'): 10, (22, 'H'): 8,
    # Hour 23
    (23, 'N'): 5, (23, 'NE'): 5, (23, 'E'): 5, (23, 'SE'): 4,
    (23, 'S'): 3, (23, 'SW'): 6, (23, 'W'): 8, (23, 'NW'): 8, (23, 'H'): 5,
    # Hour 24
    (24, 'N'): 3, (24, 'NE'): 3, (24, 'E'): 3, (24, 'SE'): 3,
    (24, 'S'): 2, (24, 'SW'): 4, (24, 'W'): 5, (24, 'NW'): 5, (24, 'H'): 4,
}


# ── Wall Group Multipliers ──────────────────────────────────────────
# Apply as: CLTD_group = CLTD_D * multiplier
# Group G uses the 'H' (Horiz Roof) column directly — no multiplier.

WALL_GROUP_MULTIPLIERS: dict[str, float] = {
    'A': 1.5,
    'B': 1.3,
    'C': 1.1,
    'D': 1.0,
    'E': 0.85,
    'F': 0.70,
}


def get_cltd(hour: int, orientation: str, wall_group: str = 'D') -> float:
    """Look up CLTD value (°C) for given hour, orientation, and wall group.

    Args:
        hour: Hour 1–24 (24-hour clock).
        orientation: Orientation string — one of N,NE,E,SE,S,SW,W,NW,H.
        wall_group: Wall group 'A' through 'G'. Default 'D'.

    Returns:
        CLTD value in °C (base conditions, before correction).
    """
    # Group G (roofs) — use the H column directly
    if wall_group == 'G':
        key = (hour, 'H')
        return float(CLTD_GROUP_D.get(key, 0.0))

    # All other groups — look up Group D value and apply multiplier
    key = (hour, orientation)
    base = CLTD_GROUP_D.get(key, 0.0)
    multiplier = WALL_GROUP_MULTIPLIERS.get(wall_group, 1.0)
    return float(base * multiplier)


# ── CLF Table — Solar through Glass ─────────────────────────────────
# Cooling Load Factors for no interior shading, latitude 32°N, July 21.
# Keys: (hour_24, orientation_str). Values: dimensionless 0.0–1.0.

CLF_SOLAR_TABLE: dict[tuple[int, str], float] = {
    # 08:00
    (8, 'N'): 0.09, (8, 'NE'): 0.54, (8, 'E'): 0.73, (8, 'SE'): 0.56,
    (8, 'S'): 0.12, (8, 'SW'): 0.06, (8, 'W'): 0.06, (8, 'NW'): 0.06, (8, 'H'): 0.37,
    # 10:00
    (10, 'N'): 0.10, (10, 'NE'): 0.30, (10, 'E'): 0.61, (10, 'SE'): 0.64,
    (10, 'S'): 0.30, (10, 'SW'): 0.08, (10, 'W'): 0.07, (10, 'NW'): 0.07, (10, 'H'): 0.64,
    # 12:00
    (12, 'N'): 0.10, (12, 'NE'): 0.10, (12, 'E'): 0.21, (12, 'SE'): 0.50,
    (12, 'S'): 0.51, (12, 'SW'): 0.21, (12, 'W'): 0.10, (12, 'NW'): 0.10, (12, 'H'): 0.84,
    # 14:00
    (14, 'N'): 0.09, (14, 'NE'): 0.09, (14, 'E'): 0.09, (14, 'SE'): 0.21,
    (14, 'S'): 0.51, (14, 'SW'): 0.50, (14, 'W'): 0.39, (14, 'NW'): 0.16, (14, 'H'): 0.84,
    # 16:00
    (16, 'N'): 0.09, (16, 'NE'): 0.09, (16, 'E'): 0.09, (16, 'SE'): 0.09,
    (16, 'S'): 0.22, (16, 'SW'): 0.58, (16, 'W'): 0.73, (16, 'NW'): 0.44, (16, 'H'): 0.64,
    # 18:00
    (18, 'N'): 0.09, (18, 'NE'): 0.09, (18, 'E'): 0.09, (18, 'SE'): 0.09,
    (18, 'S'): 0.09, (18, 'SW'): 0.28, (18, 'W'): 0.64, (18, 'NW'): 0.55, (18, 'H'): 0.27,
}

# Tabulated hours for interpolation
_CLF_HOURS = [8, 10, 12, 14, 16, 18]

# Night/early morning minimum CLF for all orientations
_CLF_NIGHT_MIN = 0.09

# All orientations
_ORIENTATIONS = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'H']


def get_clf_solar(hour: int, orientation: str, has_interior_shading: bool = False) -> float:
    """Look up or interpolate CLF for solar gain through glass.

    For hours 19:00–07:00, returns 0.09 (night minimum).
    For tabulated hours (8,10,12,14,16,18), returns exact value.
    For intermediate hours, linearly interpolates between adjacent values.

    Interior shading reduces CLF by factor of 0.5 (simplified).

    Args:
        hour: Hour 1–24.
        orientation: Orientation string.
        has_interior_shading: True if blinds/curtains present.

    Returns:
        CLF value (dimensionless).
    """
    # Night/early morning — use minimum
    if hour < 8 or hour > 18:
        clf = _CLF_NIGHT_MIN
    elif hour in _CLF_HOURS:
        # Exact table lookup
        clf = CLF_SOLAR_TABLE.get((hour, orientation), _CLF_NIGHT_MIN)
    else:
        # Linear interpolation between adjacent tabulated hours
        # Find bounding hours
        lower_hour = max(h for h in _CLF_HOURS if h <= hour)
        upper_hour = min(h for h in _CLF_HOURS if h >= hour)
        if lower_hour == upper_hour:
            clf = CLF_SOLAR_TABLE.get((lower_hour, orientation), _CLF_NIGHT_MIN)
        else:
            clf_lower = CLF_SOLAR_TABLE.get((lower_hour, orientation), _CLF_NIGHT_MIN)
            clf_upper = CLF_SOLAR_TABLE.get((upper_hour, orientation), _CLF_NIGHT_MIN)
            frac = (hour - lower_hour) / (upper_hour - lower_hour)
            clf = clf_lower + frac * (clf_upper - clf_lower)

    # Interior shading reduces CLF by approximately 0.5
    # This is a simplification of the full ASHRAE shading calculation.
    if has_interior_shading:
        clf *= 0.5

    return clf


# ── Orientation I_max Factors ───────────────────────────────────────
# Maximum solar intensity = 630 W/m² * factor
# Simplified approach for 32°N latitude, July — will be replaced
# with full solar geometry in v0.5.

I_MAX_BASE = 630.0  # W/m²

I_MAX_FACTORS: dict[str, float] = {
    'N':  0.17,
    'NE': 0.57,
    'E':  0.97,
    'SE': 0.83,
    'S':  0.62,
    'SW': 0.83,
    'W':  0.97,
    'NW': 0.57,
    'H':  1.22,
}


def get_i_max(orientation: str) -> float:
    """Return maximum solar intensity (W/m²) for an orientation.

    Uses simplified approach: 630 W/m² * orientation factor.
    This approximation is for 32°N latitude, July.
    Full solar geometry calculation will replace this in v0.5.
    """
    return I_MAX_BASE * I_MAX_FACTORS.get(orientation, 0.0)


# ── Design Conditions Database ──────────────────────────────────────
# ASHRAE 2021 HOF Appendix — Climatic Design Conditions.
# All temperatures in °C, latitude in degrees.

_DESIGN_CONDITIONS: dict[str, dict] = {
    'miami': {
        't_outdoor_db': 33.9, 't_outdoor_wb': 26.8,
        't_winter_db': 8.3, 'lat': 25.8,
    },
    'phoenix': {
        't_outdoor_db': 43.3, 't_outdoor_wb': 24.4,
        't_winter_db': 3.3, 'lat': 33.4,
    },
    'los_angeles': {
        't_outdoor_db': 32.2, 't_outdoor_wb': 21.1,
        't_winter_db': 7.2, 'lat': 33.9,
    },
    'chicago': {
        't_outdoor_db': 33.3, 't_outdoor_wb': 23.9,
        't_winter_db': -16.7, 'lat': 41.9,
    },
    'new_york': {
        't_outdoor_db': 32.8, 't_outdoor_wb': 23.9,
        't_winter_db': -8.9, 'lat': 40.6,
    },
    'london': {
        't_outdoor_db': 28.3, 't_outdoor_wb': 20.6,
        't_winter_db': -3.2, 'lat': 51.5,
    },
    'dubai': {
        't_outdoor_db': 45.0, 't_outdoor_wb': 28.0,
        't_winter_db': 12.0, 'lat': 25.2,
    },
    'singapore': {
        't_outdoor_db': 32.7, 't_outdoor_wb': 26.8,
        't_winter_db': 23.0, 'lat': 1.3,
    },
    'sydney': {
        't_outdoor_db': 33.3, 't_outdoor_wb': 22.8,
        't_winter_db': 5.0, 'lat': -33.9,
    },
    'toronto': {
        't_outdoor_db': 31.7, 't_outdoor_wb': 23.3,
        't_winter_db': -18.3, 'lat': 43.7,
    },
}


def get_design_conditions(city: str) -> dict:
    """Get ASHRAE design conditions for a city.

    Args:
        city: City name (case-insensitive).

    Returns:
        Dict with keys: 'city', 't_outdoor_db', 't_outdoor_wb',
        't_winter_db', 'lat'.

    Raises:
        DesignConditionsNotFoundError: If city not found.
    """
    key = city.lower().strip()
    if key not in _DESIGN_CONDITIONS:
        available = list_design_cities()
        raise DesignConditionsNotFoundError(
            f"City '{city}' not found in design conditions database. "
            f"Available cities: {available}. "
            f"Check list_design_cities() for the full list."
        )
    result = dict(_DESIGN_CONDITIONS[key])
    result['city'] = key
    return result


def list_design_cities() -> list[str]:
    """Return list of available city names in the design conditions database."""
    return sorted(_DESIGN_CONDITIONS.keys())
