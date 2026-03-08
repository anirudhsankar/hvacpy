"""Standard nominal equipment sizes and selection logic.

Data only + next_size_up(). No imports from other hvacpy equipment modules.
All sizes in kW.
"""

from __future__ import annotations

from hvacpy.exceptions import EquipmentSizingError

# ── Nominal Size Tables ─────────────────────────────────────────────

NOMINAL_SIZES: dict[str, list[float]] = {
    'split_residential': [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0],
    'split_light_commercial': [7.0, 8.0, 10.0, 12.5, 14.0, 16.0, 18.0, 22.5],
    'packaged_rtu_small': [7.0, 8.8, 10.5, 12.3, 14.1, 17.6, 21.1, 24.6],
    'packaged_rtu_large': [28.0, 35.0, 42.0, 52.5, 63.0, 70.0, 87.5, 105.0],
    'fan_coil_unit': [0.9, 1.2, 1.8, 2.4, 3.5, 5.3, 7.0],
    'chiller_air_cooled': [35.0, 52.0, 70.0, 87.0, 105.0, 140.0, 175.0, 210.0, 280.0, 350.0],
    'chiller_water_cooled': [175.0, 350.0, 527.0, 703.0, 880.0, 1055.0, 1230.0, 1580.0, 2110.0],
    'heat_pump_air_source': [2.0, 2.5, 3.5, 5.0, 7.0, 8.8, 10.5, 14.0],
}


def next_size_up(required_kw: float, equipment_type: str) -> float:
    """Return smallest nominal size >= required_kw.

    Args:
        required_kw: Required capacity in kW.
        equipment_type: Key into NOMINAL_SIZES dict.

    Returns:
        Nominal size in kW.

    Raises:
        EquipmentSizingError: If required exceeds all available sizes.
        ValueError: If equipment_type is unknown.
    """
    if equipment_type not in NOMINAL_SIZES:
        raise ValueError(
            f"Unknown equipment type '{equipment_type}'. "
            f"Available: {sorted(NOMINAL_SIZES.keys())}"
        )

    sizes = NOMINAL_SIZES[equipment_type]
    for size in sizes:
        if size >= required_kw:
            return size

    max_size = sizes[-1]
    raise EquipmentSizingError(
        f"Required capacity {required_kw:.1f} kW exceeds maximum available "
        f"size {max_size:.1f} kW for '{equipment_type}'. "
        f"Consider using multiple units to meet the load."
    )
