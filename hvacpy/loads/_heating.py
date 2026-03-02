"""Heating load calculations — ASHRAE steady-state heat loss method.

Implements ASHRAE HOF 2021 Chapter 18 steady-state method
for sizing heating equipment.

Conservative: no credit for solar gain or internal gains.
This is correct practice for heating equipment sizing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from hvacpy.units import Q_
from hvacpy.exceptions import HvacpyError
from hvacpy.loads._components import WallComponent, WindowComponent
from hvacpy.loads._cltd_tables import get_design_conditions
from hvacpy.loads._room import Room, Zone
from hvacpy.loads._infiltration import calculate_infiltration_heating

if TYPE_CHECKING:
    from pint import Quantity


class HeatingLoad:
    """Steady-state heating load using ASHRAE simple heat loss method.

    Conservative: no credit for solar gain or internal gains.
    This is correct practice for heating equipment sizing.

    Args:
        space:        Room or Zone.
        city:         City name for design conditions, OR provide t_winter_db.
        t_winter_db:  Outdoor winter design temperature as Quantity.
        wind_speed:   Design wind speed in m/s. Default Q_(6.7, 'm/s').
                      Affects infiltration rate via ACH adjustment.
    """

    def __init__(
        self,
        space: Room | Zone,
        city: str | None = None,
        *,
        t_winter_db: 'Quantity | None' = None,
        wind_speed: 'Quantity | None' = None,
    ) -> None:
        self._space = space

        # Resolve design conditions
        if t_winter_db is not None:
            self._t_winter = t_winter_db.to('degC').magnitude
        elif city is not None:
            dc = get_design_conditions(city)
            self._t_winter = dc['t_winter_db']
        else:
            raise HvacpyError(
                "Must provide either 'city' or 't_winter_db' for heating load."
            )

        # Wind speed
        if wind_speed is not None:
            self._wind_speed = wind_speed.to('m/s').magnitude
        else:
            self._wind_speed = 6.7  # m/s default

        # Get rooms list
        if isinstance(space, Zone):
            self._rooms = space.rooms
        else:
            self._rooms = [space]

        # Calculate
        self._calculate()

    def _calculate(self) -> None:
        """Compute steady-state heating load."""
        total_envelope = 0.0
        total_infiltration = 0.0
        self._component_details: list[tuple[str, float]] = []

        for room in self._rooms:
            t_indoor = room.t_indoor.to('degC').magnitude
            delta_t = t_indoor - self._t_winter

            # Envelope losses — walls and roofs
            for wall in room.walls:
                u_val = wall.assembly.u_value.magnitude  # W/(m²K)
                area = wall.area.to('m**2').magnitude
                q_loss = u_val * area * delta_t
                total_envelope += q_loss
                self._component_details.append(
                    (f'{room.name}: {wall.name}', q_loss)
                )

            # Envelope losses — windows
            for win in room.windows:
                u_win = win.u_factor.to('W/(m**2*K)').magnitude
                area_win = win.area.to('m**2').magnitude
                q_loss = u_win * area_win * delta_t
                total_envelope += q_loss
                self._component_details.append(
                    (f'{room.name}: {win.name}', q_loss)
                )

            # Infiltration
            volume = room.volume_m3
            q_inf = calculate_infiltration_heating(
                room.ach_infiltration, volume, delta_t, self._wind_speed
            )
            total_infiltration += q_inf
            self._component_details.append(
                (f'{room.name}: Infiltration', q_inf)
            )

        self._envelope_loss = total_envelope
        self._infiltration_loss = total_infiltration
        self._total = total_envelope + total_infiltration
        self._delta_t_val = (
            self._rooms[0].t_indoor.to('degC').magnitude - self._t_winter
        )

    # ── Properties ──────────────────────────────────────────────────

    @property
    def total(self) -> 'Quantity':
        """Total heating load = envelope + infiltration."""
        return Q_(self._total, 'W')

    @property
    def envelope_loss(self) -> 'Quantity':
        """Sum of all opaque and glazed envelope losses."""
        return Q_(self._envelope_loss, 'W')

    @property
    def infiltration_loss(self) -> 'Quantity':
        """Infiltration heat loss."""
        return Q_(self._infiltration_loss, 'W')

    @property
    def delta_t(self) -> 'Quantity':
        """T_indoor - T_outdoor_winter."""
        return Q_(self._delta_t_val, 'delta_degC')

    # ── Methods ─────────────────────────────────────────────────────

    def breakdown(self) -> str:
        """Formatted table of all components, their W value, and % of total.

        Same style as CoolingLoad.breakdown().
        """
        total = self._total

        def pct(val: float) -> str:
            if total == 0:
                return '  0.0%'
            return f'{val / total * 100:5.1f}%'

        lines: list[str] = []
        lines.append(f'Heating Load Breakdown — ΔT = {self._delta_t_val:.1f} K')
        lines.append('━' * 55)

        for label, val in self._component_details:
            lines.append(f'  {label:<32s} {val:>8.1f} W  {pct(val)}')

        lines.append('━' * 55)
        lines.append(f'  {"ENVELOPE TOTAL":<32s} {self._envelope_loss:>8.1f} W  {pct(self._envelope_loss)}')
        lines.append(f'  {"INFILTRATION TOTAL":<32s} {self._infiltration_loss:>8.1f} W  {pct(self._infiltration_loss)}')
        lines.append(f'  {"HEATING TOTAL":<32s} {self._total:>8.1f} W  100.0%')

        return '\n'.join(lines)
