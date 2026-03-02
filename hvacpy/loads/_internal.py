"""Internal gain calculations — people, lighting, equipment.

No imports from _cooling or _heating (prevents circular imports).
"""

from __future__ import annotations

# Physical constants — ASHRAE 1997 Table 3
PEOPLE_SENSIBLE_W: dict[str, int] = {
    'seated_quiet':      60,
    'office_work':       65,
    'standing_light':    70,
    'walking':           75,
    'light_bench_work':  80,
    'retail_banking':    75,
    'restaurant':        70,
    'dancing':          140,
    'heavy_work':       185,
}

PEOPLE_LATENT_W: dict[str, int] = {
    'seated_quiet':      45,
    'office_work':       55,
    'standing_light':    55,
    'walking':           55,
    'light_bench_work':  80,
    'retail_banking':    55,
    'restaurant':        80,
    'dancing':          175,
    'heavy_work':       250,
}

# Ballast factor for fluorescent lighting
# v0.3 uses 1.25 for all lighting (assumes fluorescent).
# Future version will add lighting_type parameter.
BALLAST_FACTOR = 1.25

# Equipment sensible/latent split — conservative office default.
# 70% sensible, 30% latent.
# v0.3 simplification — future versions will accept explicit split.
EQUIPMENT_SENSIBLE_FRACTION = 0.70
EQUIPMENT_LATENT_FRACTION = 0.30


def calculate_people_gain(
    count: int,
    activity: str,
    diversity: float = 1.0,
    clf: float = 1.0,
) -> tuple[float, float]:
    """Calculate sensible and latent heat gains from occupants.

    Args:
        count: Number of people.
        activity: Activity type key from PEOPLE_SENSIBLE_W.
        diversity: Fraction of gain actually present (0.0–1.0).
        clf: Cooling load factor for thermal storage effect.

    Returns:
        (sensible_W, latent_W) — both in Watts.
        Note: latent gain is NOT multiplied by CLF
        (latent gain has no thermal storage effect — instantaneous).
    """
    sensible_per = PEOPLE_SENSIBLE_W.get(activity, 65)
    latent_per = PEOPLE_LATENT_W.get(activity, 55)

    q_sensible = count * sensible_per * diversity * clf
    q_latent = count * latent_per * diversity  # No CLF for latent

    return (q_sensible, q_latent)


def calculate_lighting_gain(
    total_watts: float = 0.0,
    watts_per_m2: float = 0.0,
    floor_area_m2: float = 0.0,
    diversity: float = 1.0,
    clf: float = 1.0,
) -> float:
    """Calculate lighting heat gain (all sensible).

    Args:
        total_watts: Total installed wattage. Takes priority over watts_per_m2.
        watts_per_m2: Watts per m², used if total_watts is 0.
        floor_area_m2: Room floor area in m².
        diversity: Fraction of gain actually present.
        clf: Cooling load factor.

    Returns:
        Lighting gain in Watts (all sensible — no latent component).
    """
    if total_watts > 0:
        watts = total_watts
    else:
        watts = watts_per_m2 * floor_area_m2

    return watts * diversity * clf * BALLAST_FACTOR


def calculate_equipment_gain(
    total_watts: float = 0.0,
    watts_per_m2: float = 0.0,
    floor_area_m2: float = 0.0,
    diversity: float = 1.0,
    clf: float = 1.0,
) -> tuple[float, float]:
    """Calculate equipment heat gain split into sensible + latent.

    Args:
        total_watts: Total installed wattage. Takes priority over watts_per_m2.
        watts_per_m2: Watts per m², used if total_watts is 0.
        floor_area_m2: Room floor area in m².
        diversity: Fraction of gain actually present.
        clf: Cooling load factor.

    Returns:
        (sensible_W, latent_W) — split 70/30 (conservative office default).
        This split is a simplification for v0.3. Future versions will
        accept explicit sensible/latent split.
    """
    if total_watts > 0:
        watts = total_watts
    else:
        watts = watts_per_m2 * floor_area_m2

    q_total = watts * diversity * clf
    q_sensible = q_total * EQUIPMENT_SENSIBLE_FRACTION
    q_latent = q_total * EQUIPMENT_LATENT_FRACTION

    return (q_sensible, q_latent)
