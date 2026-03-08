"""Ventilation compliance check — ASHRAE 62.1-2022 Table 6-1.

Single-zone ventilation rate procedure.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from hvacpy.units import Q_
from hvacpy.loads._room import Room

if TYPE_CHECKING:
    from pint import Quantity

# ── ASHRAE 62.1-2022 Table 6-1 Ventilation Rates ───────────────────
# Rp = people outdoor air rate (L/s per person)
# Ra = area outdoor air rate (L/s per m²)

VENTILATION_RATES: dict[str, dict[str, float]] = {
    'office':        {'Rp': 2.5, 'Ra': 0.3},
    'conference':    {'Rp': 2.5, 'Ra': 0.3},
    'classroom':     {'Rp': 3.8, 'Ra': 0.6},
    'retail':        {'Rp': 1.7, 'Ra': 0.6},
    'restaurant':    {'Rp': 3.8, 'Ra': 0.9},
    'gym':           {'Rp': 5.0, 'Ra': 0.9},
    'hotel_room':    {'Rp': 2.5, 'Ra': 0.3},
    'hospital_ward': {'Rp': 2.5, 'Ra': 0.6},
    'data_centre':   {'Rp': 0.0, 'Ra': 0.6},
    'corridor':      {'Rp': 0.0, 'Ra': 0.3},
}


class VentilationCheck:
    """ASHRAE 62.1-2022 single-zone ventilation compliance check.

    Vz = Rp * Pz + Ra * Az  [L/s]

    Args:
        room: Room object (provides floor_area_m2 and occupant count).
        supply_airflow: Total supply airflow as Quantity (m³/s or L/s).
        space_type: Key into VENTILATION_RATES.
        oa_fraction: Outdoor air fraction of supply. Default 0.15.
    """

    def __init__(
        self,
        room: Room,
        supply_airflow: 'Quantity',
        space_type: str,
        oa_fraction: float = 0.15,
    ) -> None:
        if space_type not in VENTILATION_RATES:
            raise ValueError(
                f"Unknown space type '{space_type}'. "
                f"Available: {sorted(VENTILATION_RATES.keys())}"
            )

        rates = VENTILATION_RATES[space_type]
        rp = rates['Rp']
        ra = rates['Ra']

        # Occupant count from internal gains
        pz = 0
        for gain in room.internal_gains:
            if gain.gain_type == 'people':
                pz += gain.count

        az = room.floor_area_m2

        # Required outdoor airflow (L/s)
        self._required_oa_ls = rp * pz + ra * az

        # Actual outdoor airflow (L/s)
        supply_m3s = supply_airflow.to('m**3/s').magnitude
        actual_oa_m3s = supply_m3s * oa_fraction
        self._actual_oa_ls = actual_oa_m3s * 1000.0  # m³/s -> L/s

        self._space_type = space_type
        self._oa_fraction = oa_fraction

    @property
    def required_oa_flow(self) -> 'Quantity':
        """Required outdoor air flow in L/s."""
        return Q_(self._required_oa_ls, 'L/s')

    @property
    def actual_oa_flow(self) -> 'Quantity':
        """Actual outdoor air flow in L/s."""
        return Q_(self._actual_oa_ls, 'L/s')

    @property
    def compliant(self) -> bool:
        """True if actual OA >= required OA."""
        return self._actual_oa_ls >= self._required_oa_ls

    @property
    def deficit(self) -> 'Quantity':
        """Deficit in L/s (0 if compliant)."""
        if self.compliant:
            return Q_(0, 'L/s')
        return Q_(self._required_oa_ls - self._actual_oa_ls, 'L/s')

    def summary(self) -> str:
        """Compliance summary string."""
        if self.compliant:
            return (
                f"COMPLIANT - {self._actual_oa_ls:.1f} L/s provided, "
                f"{self._required_oa_ls:.1f} required"
            )
        else:
            return (
                f"NON-COMPLIANT - deficit {self.deficit.magnitude:.1f} L/s "
                f"({self._actual_oa_ls:.1f} provided, "
                f"{self._required_oa_ls:.1f} required)"
            )
