"""Cooling equipment sizing classes — ASHRAE HSE 2020.

SplitSystem, PackagedRTU, FanCoilUnit, Chiller.
The engineer is always in charge — summary() shows required vs nominal,
all warnings advisory, never refuses to complete a calculation.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from hvacpy.units import Q_
from hvacpy.equipment._nominal_sizes import next_size_up
from hvacpy.equipment._airflow import airflow_from_cooling_load

if TYPE_CHECKING:
    from pint import Quantity

# ── Physical Constants ──────────────────────────────────────────────

OVERSIZING_WARNING_FRACTION  = 0.25   # warn if selected > required * 1.25
OVERSIZING_CRITICAL_FRACTION = 0.50   # critical if > required * 1.50
T_SUPPLY_AIR_COOLING_C = 13.0         # °C default cooling supply air
T_SUPPLY_AIR_HEATING_C = 40.0         # °C default heating supply air
RHO_AIR_KG_M3          = 1.2          # kg/m³ standard air density
FRICTION_RATE_PA_M     = 0.8          # Pa/m ASHRAE recommended equal friction
V_MAX_MAIN_DUCT_M_S    = 7.5          # m/s max main supply duct
V_MAX_BRANCH_DUCT_M_S  = 5.0          # m/s max branch duct
V_MAX_RETURN_DUCT_M_S  = 5.0          # m/s max return duct
T_TEST_OUTDOOR_C       = 35.0         # °C ASHRAE 210/240 cooling test
T_TEST_HEATING_C       = 8.3          # °C ASHRAE 210/240 heating test

# Chilled water constants
CP_WATER = 4186.0     # J/(kg·K)
RHO_WATER = 1000.0    # kg/m³


# ── Base Class ──────────────────────────────────────────────────────

class CoolingEquipment:
    """Base class for cooling equipment sizing.

    Not exported — use SplitSystem, PackagedRTU, FanCoilUnit, or Chiller.
    """

    def __init__(self, cooling_load, equipment_type: str, cop_rated: float) -> None:
        self._cooling_load = cooling_load
        self._required_kw = cooling_load.peak_total.to('kW').magnitude
        self._sensible_kw = cooling_load.peak_sensible.to('kW').magnitude
        self._latent_kw = cooling_load.peak_latent.to('kW').magnitude
        self._shr = cooling_load.sensible_heat_ratio
        self._cop_rated = cop_rated
        self._equipment_type = equipment_type
        self._nominal_kw = next_size_up(self._required_kw, equipment_type)
        self._airflow = airflow_from_cooling_load(cooling_load)

    @property
    def required_capacity(self) -> 'Quantity':
        """Peak total cooling load in kW."""
        return Q_(self._required_kw, 'kW')

    @property
    def nominal_capacity(self) -> 'Quantity':
        """Selected standard nominal size in kW."""
        return Q_(self._nominal_kw, 'kW')

    @property
    def oversizing_ratio(self) -> float:
        """Ratio of nominal to required capacity."""
        if self._required_kw == 0:
            return 1.0
        return self._nominal_kw / self._required_kw

    @property
    def oversizing_warning(self) -> str | None:
        """None if <1.25, 'WARNING' if 1.25-1.50, 'CRITICAL' if >1.50."""
        ratio = self.oversizing_ratio
        if ratio > 1.0 + OVERSIZING_CRITICAL_FRACTION:
            return 'CRITICAL'
        elif ratio > 1.0 + OVERSIZING_WARNING_FRACTION:
            return 'WARNING'
        return None

    @property
    def supply_airflow(self) -> 'Quantity':
        """Supply airflow in m³/s."""
        return self._airflow

    @property
    def input_power_kw(self) -> 'Quantity':
        """Electrical input power = nominal / COP."""
        return Q_(self._nominal_kw / self._cop_rated, 'kW')

    def _warning_text(self) -> str:
        w = self.oversizing_warning
        if w is None:
            return 'within 25% limit'
        elif w == 'WARNING':
            return 'OVERSIZED 25-50%'
        else:
            return 'CRITICALLY OVERSIZED >50%'

    def _warning_section(self) -> str:
        w = self.oversizing_warning
        if w is None:
            return '|   None                                      |'
        elif w == 'WARNING':
            return '|   ⚠ Equipment oversized by >25%              |'
        else:
            return '|   ⚠ CRITICAL: Equipment oversized by >50%    |'

    def summary(self) -> str:
        """Box-format equipment sizing summary."""
        airflow_m3h = self._airflow.magnitude * 3600
        label = self._label()
        lines = [
            '+================================================+',
            '| EQUIPMENT SIZING SUMMARY                       |',
            f'| {label:<47s}|',
            '+================================================+',
            '| LOAD                                           |',
            f'|   Peak total:    {self._required_kw:>6.2f} kW{" ":<20s}|',
            f'|   Peak sensible: {self._sensible_kw:>6.2f} kW  (SHR {self._shr:.3f}){" ":<6s}|',
            f'|   Peak latent:   {self._latent_kw:>6.2f} kW{" ":<20s}|',
            '+================================================+',
            '| SELECTED EQUIPMENT                             |',
            f'|   Required:      {self._required_kw:>6.2f} kW{" ":<20s}|',
            f'|   Nominal:       {self._nominal_kw:>6.2f} kW  (next std size){" ":<3s}|',
            f'|   Oversizing:    {self.oversizing_ratio:>6.3f}     {self._warning_text():<14s}|',
            f'|   COP:           {self._cop_rated:>6.1f}{" ":<24s}|',
            f'|   Input power:   {self.input_power_kw.magnitude:>6.2f} kW{" ":<20s}|',
            '+================================================+',
            '| AIRFLOW                                        |',
            f'|   Supply:        {self._airflow.magnitude:>6.3f} m3/s  ({airflow_m3h:.0f} m3/h){" ":<4s}|',
            f'|   Supply temp:   {T_SUPPLY_AIR_COOLING_C:>5.1f} degC{" ":<19s}|',
            '+================================================+',
            '| WARNINGS                                       |',
            self._warning_section(),
            '+================================================+',
        ]
        return '\n'.join(lines)

    def _label(self) -> str:
        return 'Cooling Equipment'

    def to_dict(self) -> dict:
        """All properties as plain floats/strings."""
        return {
            'equipment_type': self._equipment_type,
            'required_capacity_kw': self._required_kw,
            'nominal_capacity_kw': self._nominal_kw,
            'oversizing_ratio': self.oversizing_ratio,
            'oversizing_warning': self.oversizing_warning,
            'cop_rated': self._cop_rated,
            'input_power_kw': self.input_power_kw.magnitude,
            'supply_airflow_m3s': self._airflow.magnitude,
        }


# ── SplitSystem ─────────────────────────────────────────────────────

class SplitSystem(CoolingEquipment):
    """Split system (residential or light commercial).

    Selects 'split_residential' if required < 7 kW,
    else 'split_light_commercial'.
    """

    def __init__(self, cooling_load, cop_rated: float = 3.5,
                 multi_split: bool = False) -> None:
        required_kw = cooling_load.peak_total.to('kW').magnitude
        if required_kw < 7.0:
            eq_type = 'split_residential'
            self._subtype = 'residential'
        else:
            eq_type = 'split_light_commercial'
            self._subtype = 'light_commercial'
        self._multi_split = multi_split
        super().__init__(cooling_load, eq_type, cop_rated)

    @property
    def equipment_subtype(self) -> str:
        """'residential' or 'light_commercial'."""
        return self._subtype

    def _label(self) -> str:
        sub = self._subtype.replace('_', ' ').title()
        label = f'Split System ({sub})'
        if self._multi_split:
            n = math.ceil(self._required_kw / 6.0)
            label += f' — {n} indoor units'
        return label


# ── PackagedRTU ─────────────────────────────────────────────────────

class PackagedRTU(CoolingEquipment):
    """Packaged rooftop unit (small or large).

    Selects 'packaged_rtu_small' if required <= 24.6 kW,
    else 'packaged_rtu_large'.
    """

    def __init__(self, cooling_load, cop_rated: float = 3.2,
                 has_economiser: bool = False,
                 has_gas_heat: bool = False) -> None:
        required_kw = cooling_load.peak_total.to('kW').magnitude
        if required_kw <= 24.6:
            eq_type = 'packaged_rtu_small'
        else:
            eq_type = 'packaged_rtu_large'
        self._has_economiser = has_economiser
        self._has_gas_heat = has_gas_heat
        super().__init__(cooling_load, eq_type, cop_rated)

    @property
    def eer(self) -> float:
        """Energy Efficiency Ratio = COP * 3.412 (BTU/Wh)."""
        return self._cop_rated * 3.412

    def _label(self) -> str:
        features = []
        if self._has_economiser:
            features.append('Economiser')
        if self._has_gas_heat:
            features.append('Gas Heat')
        extra = f' — {", ".join(features)}' if features else ''
        return f'Packaged RTU{extra}'


# ── FanCoilUnit ─────────────────────────────────────────────────────

class FanCoilUnit(CoolingEquipment):
    """Fan coil unit with chilled water.

    Calculates chilled water flow rate.
    """

    def __init__(self, cooling_load, chilled_water_supply_t=None,
                 chilled_water_return_t=None, cop_rated: float = 4.5) -> None:
        self._chw_supply_c = (
            chilled_water_supply_t.to('degC').magnitude
            if chilled_water_supply_t is not None else 7.0
        )
        self._chw_return_c = (
            chilled_water_return_t.to('degC').magnitude
            if chilled_water_return_t is not None else 12.0
        )
        super().__init__(cooling_load, 'fan_coil_unit', cop_rated)

    @property
    def delta_t_chw(self) -> 'Quantity':
        """Chilled water ΔT in K."""
        return Q_(self._chw_return_c - self._chw_supply_c, 'delta_degC')

    @property
    def chw_flow_rate(self) -> 'Quantity':
        """Chilled water flow rate in L/s.

        V_dot = Q_total / (CP_water * delta_T * rho_water)
        """
        q_w = self._required_kw * 1000.0  # kW -> W
        delta_t = self._chw_return_c - self._chw_supply_c
        m_dot = q_w / (CP_WATER * delta_t)  # kg/s
        v_dot_ls = m_dot / RHO_WATER * 1000.0  # m³/s -> L/s
        return Q_(v_dot_ls, 'L/s')

    def _label(self) -> str:
        return 'Fan Coil Unit'


# ── Chiller ─────────────────────────────────────────────────────────

class Chiller(CoolingEquipment):
    """Chiller (air-cooled or water-cooled).

    Supports N+1 redundancy and condenser heat rejection calculation.
    """

    def __init__(self, cooling_load, chiller_type: str = 'air_cooled',
                 cop_rated: float | None = None,
                 n_units: int = 1,
                 redundancy: str = 'none') -> None:
        # COP defaults
        if cop_rated is None:
            cop_rated = 3.2 if chiller_type == 'air_cooled' else 5.5

        self._chiller_type = chiller_type
        self._n_units = n_units
        self._redundancy = redundancy

        # Determine equipment type key
        eq_type = (
            'chiller_air_cooled' if chiller_type == 'air_cooled'
            else 'chiller_water_cooled'
        )

        # N+1 redundancy: size each unit for required/(n_units-1)
        required_kw = cooling_load.peak_total.to('kW').magnitude
        if redundancy == 'n+1':
            from hvacpy.exceptions import EquipmentSizingError
            if n_units < 2:
                raise EquipmentSizingError(
                    "N+1 redundancy requires n_units >= 2. "
                    f"Got n_units={n_units}."
                )
            per_unit_kw = required_kw / (n_units - 1)
        else:
            per_unit_kw = required_kw / n_units if n_units > 1 else required_kw

        self._per_unit_required_kw = per_unit_kw
        self._per_unit_nominal_kw = next_size_up(per_unit_kw, eq_type)

        super().__init__(cooling_load, eq_type, cop_rated)
        # Override nominal with per-unit size (base class sizes for total)
        self._nominal_kw = self._per_unit_nominal_kw

    @property
    def capacity_per_unit(self) -> 'Quantity':
        """Nominal capacity per chiller unit in kW."""
        return Q_(self._per_unit_nominal_kw, 'kW')

    @property
    def condenser_heat_rejection(self) -> 'Quantity':
        """Total condenser heat rejection in kW.

        Q_cond = Q_total * (1 + 1/COP)
        """
        q_cond = self._required_kw * (1.0 + 1.0 / self._cop_rated)
        return Q_(q_cond, 'kW')

    @property
    def cooling_tower_flow(self) -> 'Quantity | None':
        """Cooling tower water flow rate in L/s. None if air-cooled.

        V_dot = Q_cond / (CP_water * delta_T_tower * rho_water)
        delta_T_tower default = 5K
        """
        if self._chiller_type == 'air_cooled':
            return None
        q_cond_w = self.condenser_heat_rejection.magnitude * 1000.0
        delta_t_tower = 5.0  # K
        m_dot = q_cond_w / (CP_WATER * delta_t_tower)  # kg/s
        v_dot_ls = m_dot / RHO_WATER * 1000.0  # L/s
        return Q_(v_dot_ls, 'L/s')

    def _label(self) -> str:
        ct = self._chiller_type.replace('_', '-').title()
        parts = [f'Chiller ({ct})']
        if self._n_units > 1:
            parts.append(f'{self._n_units} units')
        if self._redundancy == 'n+1':
            parts.append('N+1')
        return ' — '.join(parts)
