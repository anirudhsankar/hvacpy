"""Air-source heat pump sizing — ASHRAE HSE 2020 Ch.49.

Handles both cooling and heating modes with COP correction curves,
heating capacity derating, and supplemental heat calculation.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from hvacpy.units import Q_
from hvacpy.equipment._nominal_sizes import next_size_up
from hvacpy.equipment._airflow import airflow_from_cooling_load

if TYPE_CHECKING:
    from pint import Quantity


def _cop_correction_cooling(cop_rated: float, t_outdoor_c: float) -> float:
    """COP at actual outdoor temperature for cooling mode.

    COP_cool(T) = COP_rated * (1 - 0.013*(T - 35.0))
    Valid 20–46°C. Minimum 1.5.
    """
    factor = 1.0 - 0.013 * (t_outdoor_c - 35.0)
    return max(cop_rated * factor, 1.5)


def _cop_correction_heating(cop_rated: float, t_outdoor_c: float) -> float:
    """COP at actual outdoor temperature for heating mode.

    COP_heat(T) = COP_rated * (1 + 0.025*(T - 8.3))
    Valid -15 to 15°C. Minimum 1.0.
    """
    factor = 1.0 + 0.025 * (t_outdoor_c - 8.3)
    return max(cop_rated * factor, 1.0)


def _heating_capacity_at_temp(
    nominal_cooling_kw: float, t_outdoor_c: float,
) -> float:
    """Actual heating capacity at design outdoor temperature.

    Q_heat_rated = Q_cool_nominal * 1.15
    Q_heat_actual(T) = Q_heat_rated * (1 + 0.020*(T - 8.3))
    Clamped minimum = Q_cool_nominal * 0.50
    """
    q_heat_rated = nominal_cooling_kw * 1.15
    factor = 1.0 + 0.020 * (t_outdoor_c - 8.3)
    q_actual = q_heat_rated * factor
    return max(q_actual, nominal_cooling_kw * 0.50)


class AirSourceHeatPump:
    """Air-source heat pump sizing for both cooling and heating.

    Determines binding mode, COP corrections, heating coverage,
    and supplemental heat requirements.
    """

    def __init__(
        self,
        cooling_load,
        heating_load,
        cop_rated_cooling: float = 3.5,
        cop_rated_heating: float = 3.8,
        t_outdoor_cooling: 'Quantity | None' = None,
        t_outdoor_heating: 'Quantity | None' = None,
    ) -> None:
        self._cooling_load = cooling_load
        self._heating_load = heating_load
        self._cop_rated_cooling = cop_rated_cooling
        self._cop_rated_heating = cop_rated_heating

        # Design temperatures
        self._t_cool_c = (
            t_outdoor_cooling.to('degC').magnitude
            if t_outdoor_cooling is not None else 35.0
        )
        self._t_heat_c = (
            t_outdoor_heating.to('degC').magnitude
            if t_outdoor_heating is not None else 8.3
        )

        # Required capacities
        self._req_cooling_kw = cooling_load.peak_total.to('kW').magnitude
        self._req_heating_kw = heating_load.total.to('kW').magnitude

        # Size by cooling load
        self._nominal_kw = next_size_up(
            self._req_cooling_kw, 'heat_pump_air_source'
        )

        # Check heating capacity at design conditions
        self._actual_heating_kw = _heating_capacity_at_temp(
            self._nominal_kw, self._t_heat_c,
        )

        # Determine binding mode
        if self._req_heating_kw > self._actual_heating_kw:
            # Heating is more demanding — but we still size by cooling
            # since heat pump nominal is defined by cooling
            self._binding_mode = 'heating'
        else:
            self._binding_mode = 'cooling'

        # COP at design conditions
        self._cop_design_cooling = _cop_correction_cooling(
            cop_rated_cooling, self._t_cool_c,
        )
        self._cop_design_heating = _cop_correction_heating(
            cop_rated_heating, self._t_heat_c,
        )

        # Airflow
        self._airflow = airflow_from_cooling_load(cooling_load)

    # ── Properties ──────────────────────────────────────────────────

    @property
    def binding_mode(self) -> str:
        """'cooling' or 'heating' — which determined nominal size."""
        return self._binding_mode

    @property
    def nominal_capacity_kw(self) -> 'Quantity':
        """Nominal cooling capacity from heat pump table."""
        return Q_(self._nominal_kw, 'kW')

    @property
    def cooling_oversizing(self) -> float:
        """nominal / required_cooling."""
        if self._req_cooling_kw == 0:
            return 1.0
        return self._nominal_kw / self._req_cooling_kw

    @property
    def heating_coverage(self) -> float:
        """actual_heating_at_design / required_heating."""
        if self._req_heating_kw == 0:
            return 1.0
        return self._actual_heating_kw / self._req_heating_kw

    @property
    def needs_supplemental_heat(self) -> bool:
        """True if heating_coverage < 1.0."""
        return self.heating_coverage < 1.0

    @property
    def supplemental_heat_kw(self) -> 'Quantity':
        """Required backup heating. 0 if not needed."""
        if not self.needs_supplemental_heat:
            return Q_(0, 'kW')
        deficit = self._req_heating_kw - self._actual_heating_kw
        return Q_(max(deficit, 0), 'kW')

    @property
    def cop_at_design_cooling(self) -> float:
        """COP at t_outdoor_cooling."""
        return self._cop_design_cooling

    @property
    def cop_at_design_heating(self) -> float:
        """COP at t_outdoor_heating."""
        return self._cop_design_heating

    @property
    def supply_airflow(self) -> 'Quantity':
        """Supply airflow in m³/s."""
        return self._airflow

    # ── Methods ─────────────────────────────────────────────────────

    def summary(self) -> str:
        """Box format showing both modes, binding, coverage, supplemental."""
        airflow_m3h = self._airflow.magnitude * 3600
        supp = (f'{self.supplemental_heat_kw.magnitude:.2f} kW'
                if self.needs_supplemental_heat else 'Not required')

        lines = [
            '+================================================+',
            '| HEAT PUMP SIZING SUMMARY                       |',
            '| Air-Source Heat Pump                            |',
            '+================================================+',
            '| COOLING MODE                                   |',
            f'|   Required:      {self._req_cooling_kw:>6.2f} kW{" ":<20s}|',
            f'|   Nominal:       {self._nominal_kw:>6.2f} kW{" ":<20s}|',
            f'|   Oversizing:    {self.cooling_oversizing:>6.3f}{" ":<24s}|',
            f'|   COP at design: {self._cop_design_cooling:>5.2f}  ({self._t_cool_c:.0f}°C){" ":<13s}|',
            '+================================================+',
            '| HEATING MODE                                   |',
            f'|   Required:      {self._req_heating_kw:>6.2f} kW{" ":<20s}|',
            f'|   HP capacity:   {self._actual_heating_kw:>6.2f} kW  (at {self._t_heat_c:.0f}°C){" ":<6s}|',
            f'|   Coverage:      {self.heating_coverage:>6.1%}{" ":<24s}|',
            f'|   COP at design: {self._cop_design_heating:>5.2f}  ({self._t_heat_c:.0f}°C){" ":<13s}|',
            f'|   Supplemental:  {supp:<30s}|',
            '+================================================+',
            f'| BINDING MODE:    {self._binding_mode.upper():<30s}|',
            f'| Supply airflow:  {self._airflow.magnitude:.3f} m3/s  ({airflow_m3h:.0f} m3/h){" ":<4s}|',
            '+================================================+',
        ]
        return '\n'.join(lines)
