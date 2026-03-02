"""Infiltration load calculations.

No imports from _cooling or _heating (prevents circular imports).
"""

from __future__ import annotations

# Physical constants — consistent with hvacpy.psychrometrics._equations
DENSITY_AIR = 1.2        # kg/m³ — standard air density (v0.3 fixed)
CP_DA = 1006.0           # J/(kg·K) — specific heat of dry air
H_FG_0 = 2_501_000.0     # J/kg — enthalpy of vaporisation at 0°C

# Default humidity ratios (used when AirState is not provided)
W_OUTDOOR_DEFAULT = 0.010    # kg/kg — moderate climate outdoor
W_INDOOR_DEFAULT = 0.0085    # kg/kg — 24°C, ~50% RH


def calculate_infiltration_mass_flow(
    ach: float,
    volume_m3: float,
) -> float:
    """Calculate infiltration mass flow rate.

    Args:
        ach: Air changes per hour.
        volume_m3: Room volume in m³.

    Returns:
        Mass flow rate in kg/s.
    """
    return DENSITY_AIR * ach * volume_m3 / 3600.0


def calculate_infiltration_sensible(
    m_dot: float,
    t_outdoor_c: float,
    t_indoor_c: float,
) -> float:
    """Calculate sensible infiltration load.

    Args:
        m_dot: Mass flow rate in kg/s.
        t_outdoor_c: Outdoor temperature in °C.
        t_indoor_c: Indoor temperature in °C.

    Returns:
        Sensible infiltration load in Watts.
    """
    return m_dot * CP_DA * (t_outdoor_c - t_indoor_c)


def calculate_infiltration_latent(
    m_dot: float,
    w_outdoor: float | None = None,
    w_indoor: float | None = None,
) -> float:
    """Calculate latent infiltration load.

    Args:
        m_dot: Mass flow rate in kg/s.
        w_outdoor: Outdoor humidity ratio (kg/kg). Default 0.010.
        w_indoor: Indoor humidity ratio (kg/kg). Default 0.0085.

    Returns:
        Latent infiltration load in Watts.
    """
    w_out = w_outdoor if w_outdoor is not None else W_OUTDOOR_DEFAULT
    w_in = w_indoor if w_indoor is not None else W_INDOOR_DEFAULT
    return m_dot * H_FG_0 * (w_out - w_in)


def calculate_infiltration_heating(
    ach: float,
    volume_m3: float,
    delta_t: float,
    wind_speed_ms: float = 6.7,
) -> float:
    """Calculate infiltration heat loss for heating load.

    Wind correction applies: ACH_heating = ACH * (wind_speed / 6.7)^0.5

    Args:
        ach: Base air changes per hour.
        volume_m3: Room volume in m³.
        delta_t: T_indoor - T_outdoor_winter in K.
        wind_speed_ms: Design wind speed in m/s. Default 6.7.

    Returns:
        Infiltration heat loss in Watts (positive = heat loss).
    """
    # Wind correction per ASHRAE HOF 2021
    ach_heating = ach * (wind_speed_ms / 6.7) ** 0.5
    m_dot = DENSITY_AIR * ach_heating * volume_m3 / 3600.0
    return m_dot * CP_DA * delta_t
