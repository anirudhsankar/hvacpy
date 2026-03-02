"""Private psychrometric equations module.

All psychrometric math as pure functions that take and return plain
Python floats in SI units. This is the computational engine.
AirState calls these functions — never the other way around.

No pint Quantities enter or leave this module. All values are SI:
  - Temperature: °C
  - Pressure: Pa
  - Humidity ratio: kg/kg
  - Enthalpy: J/kg
  - Specific volume: m³/kg

Equations are from ASHRAE Handbook of Fundamentals 2021 Chapter 1,
implemented via the psychrolib library.
"""

import psychrolib

# Initialise psychrolib to SI mode — exactly once at module import.
psychrolib.SetUnitSystem(psychrolib.SI)

# ── Physical Constants ──────────────────────────────────────────────
P_STD_PA = 101_325.0     # Pa — standard atmospheric pressure (ISO 2533)
T_ABS_ZERO = 273.15      # K  — 0°C in Kelvin
R_DA = 287.042            # J/(kg·K) — gas constant for dry air (HOF 2021 Ch.1)
R_WV = 461.524            # J/(kg·K) — gas constant for water vapour
CP_DA = 1006.0            # J/(kg·K) — specific heat dry air at constant pressure
CP_WV = 1805.0            # J/(kg·K) — specific heat water vapour
H_FG_0 = 2_501_000.0     # J/kg — enthalpy of vaporisation at 0°C (HOF 2021 Eq.1-32)


# ── Saturation Vapour Pressure ──────────────────────────────────────

def sat_vap_pressure(t_c: float) -> float:
    """Saturation vapour pressure in Pa at temperature t_c.

    Uses ASHRAE HOF 2021 Eq. 1-5 (ice, T < 0°C) and 1-6
    (water, T ≥ 0°C) via psychrolib.

    Args:
        t_c: Dry bulb temperature in °C. Valid range: -100 to 200.

    Returns:
        Saturation vapour pressure in Pa.
    """
    return psychrolib.GetSatVapPres(t_c)


# ── Core Psychrometric Functions ────────────────────────────────────

def humidity_ratio_from_rh(
    t_db_c: float,
    rh: float,
    p_pa: float = P_STD_PA,
) -> float:
    """Humidity ratio W (kg/kg) from dry bulb and relative humidity.

    Args:
        t_db_c: Dry bulb temperature in °C.
        rh: Relative humidity as decimal 0.0–1.0.
        p_pa: Atmospheric pressure in Pa.

    Returns:
        Humidity ratio in kg water / kg dry air.
    """
    return psychrolib.GetHumRatioFromRelHum(t_db_c, rh, p_pa)


def humidity_ratio_from_wet_bulb(
    t_db_c: float,
    t_wb_c: float,
    p_pa: float = P_STD_PA,
) -> float:
    """Humidity ratio W (kg/kg) from dry bulb and wet bulb temps.

    Args:
        t_db_c: Dry bulb temperature in °C.
        t_wb_c: Wet bulb temperature in °C. Must be ≤ t_db_c.
        p_pa: Atmospheric pressure in Pa.

    Returns:
        Humidity ratio in kg water / kg dry air.
    """
    return psychrolib.GetHumRatioFromTWetBulb(t_db_c, t_wb_c, p_pa)


def humidity_ratio_from_dew_point(
    t_dp_c: float,
    p_pa: float = P_STD_PA,
) -> float:
    """Humidity ratio W (kg/kg) from dew point temperature.

    Args:
        t_dp_c: Dew point temperature in °C.
        p_pa: Atmospheric pressure in Pa.

    Returns:
        Humidity ratio in kg water / kg dry air.
    """
    return psychrolib.GetHumRatioFromTDewPoint(t_dp_c, p_pa)


def rh_from_humidity_ratio(
    t_db_c: float,
    W: float,
    p_pa: float = P_STD_PA,
) -> float:
    """Relative humidity (0.0–1.0) from dry bulb and humidity ratio.

    Args:
        t_db_c: Dry bulb temperature in °C.
        W: Humidity ratio in kg/kg.
        p_pa: Atmospheric pressure in Pa.

    Returns:
        Relative humidity as decimal 0.0–1.0.
    """
    return psychrolib.GetRelHumFromHumRatio(t_db_c, W, p_pa)


def dew_point_from_humidity_ratio(
    t_db_c: float,
    W: float,
    p_pa: float = P_STD_PA,
) -> float:
    """Dew point temperature (°C) from humidity ratio.

    Args:
        t_db_c: Dry bulb temperature in °C. Used by psychrolib
            for bounds validation.
        W: Humidity ratio in kg/kg.
        p_pa: Atmospheric pressure in Pa.

    Returns:
        Dew point temperature in °C.

    Note:
        psychrolib.GetTDewPointFromHumRatio takes
        (TDryBulb, HumRatio, Pressure).
    """
    return psychrolib.GetTDewPointFromHumRatio(t_db_c, W, p_pa)


def wet_bulb_from_humidity_ratio(
    t_db_c: float,
    W: float,
    p_pa: float = P_STD_PA,
) -> float:
    """Wet bulb temperature (°C) from dry bulb and humidity ratio.

    Args:
        t_db_c: Dry bulb temperature in °C.
        W: Humidity ratio in kg/kg.
        p_pa: Atmospheric pressure in Pa.

    Returns:
        Wet bulb temperature in °C.
    """
    return psychrolib.GetTWetBulbFromHumRatio(t_db_c, W, p_pa)


def enthalpy_from_humidity_ratio(
    t_db_c: float,
    W: float,
) -> float:
    """Specific enthalpy (J/kg dry air) from dry bulb and humidity ratio.

    Uses HOF 2021 Eq. 1-32:
        h = CP_DA * t_db + W * (H_FG_0 + CP_WV * t_db)

    Args:
        t_db_c: Dry bulb temperature in °C.
        W: Humidity ratio in kg/kg.

    Returns:
        Specific enthalpy in J/kg dry air.

    Note:
        SPEC CONCERN: The specification states that psychrolib
        returns kJ/kg and needs to be multiplied by 1000.
        In fact, psychrolib SI mode returns J/kg directly.
        No multiplication is needed.
    """
    return psychrolib.GetMoistAirEnthalpy(t_db_c, W)


def specific_volume(
    t_db_c: float,
    W: float,
    p_pa: float = P_STD_PA,
) -> float:
    """Specific volume (m³/kg dry air).

    Args:
        t_db_c: Dry bulb temperature in °C.
        W: Humidity ratio in kg/kg.
        p_pa: Atmospheric pressure in Pa.

    Returns:
        Specific volume in m³/kg dry air.
    """
    return psychrolib.GetMoistAirVolume(t_db_c, W, p_pa)


def density(
    t_db_c: float,
    W: float,
    p_pa: float = P_STD_PA,
) -> float:
    """Density of moist air (kg/m³).

    Derived from specific volume: density = 1 / specific_volume.
    Not wrapped from psychrolib directly.

    Args:
        t_db_c: Dry bulb temperature in °C.
        W: Humidity ratio in kg/kg.
        p_pa: Atmospheric pressure in Pa.

    Returns:
        Density in kg/m³.
    """
    return 1.0 / specific_volume(t_db_c, W, p_pa)


def humidity_ratio_from_enthalpy_and_dbt(
    h_j_kg: float,
    t_db_c: float,
) -> float:
    """Recover humidity ratio W from enthalpy and dry bulb.

    Inverse of enthalpy equation (HOF 2021 Eq. 1-32):
        W = (h - CP_DA * t_db) / (H_FG_0 + CP_WV * t_db)

    Pure math — no psychrolib.

    Args:
        h_j_kg: Specific enthalpy in J/kg dry air.
        t_db_c: Dry bulb temperature in °C.

    Returns:
        Humidity ratio in kg/kg.
    """
    return (h_j_kg - CP_DA * t_db_c) / (H_FG_0 + CP_WV * t_db_c)


# ── Adiabatic Mixing ────────────────────────────────────────────────

def mix_airstreams(
    t_db1: float,
    W1: float,
    m1: float,
    t_db2: float,
    W2: float,
    m2: float,
    p_pa: float = P_STD_PA,
) -> tuple[float, float, float]:
    """Mix two dry-air mass flows adiabatically.

    Pure mass and energy balance — no psychrolib needed.
    HOF 2021 Section 1.4.

    Args:
        t_db1: Dry bulb temperature of stream 1 in °C.
        W1: Humidity ratio of stream 1 in kg/kg.
        m1: Mass flow rate of stream 1 in kg/s dry air. Must be > 0.
        t_db2: Dry bulb temperature of stream 2 in °C.
        W2: Humidity ratio of stream 2 in kg/kg.
        m2: Mass flow rate of stream 2 in kg/s dry air. Must be > 0.
        p_pa: Atmospheric pressure in Pa.

    Returns:
        Tuple of (t_db_mix_c, W_mix, rh_mix) all as floats.
    """
    h1 = enthalpy_from_humidity_ratio(t_db1, W1)
    h2 = enthalpy_from_humidity_ratio(t_db2, W2)

    m_total = m1 + m2
    W_mix = (m1 * W1 + m2 * W2) / m_total
    h_mix = (m1 * h1 + m2 * h2) / m_total

    # Recover dry bulb from mixed enthalpy and humidity ratio
    t_db_mix = (h_mix - H_FG_0 * W_mix) / (CP_DA + CP_WV * W_mix)

    rh_mix = rh_from_humidity_ratio(t_db_mix, W_mix, p_pa)

    return (t_db_mix, W_mix, rh_mix)
