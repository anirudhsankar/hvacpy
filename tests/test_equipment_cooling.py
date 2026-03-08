"""Tests for supply airflow and cooling equipment — v0.4.

Test groups A (airflow) and B (cooling equipment) from the spec.
"""

from __future__ import annotations

import math
from types import SimpleNamespace
from unittest.mock import PropertyMock

import pytest

from hvacpy.units import Q_
from hvacpy.exceptions import AirflowCalculationError, EquipmentSizingError
from hvacpy.equipment._airflow import (
    supply_airflow_cooling,
    supply_airflow_heating,
    airflow_from_cooling_load,
)
from hvacpy.equipment._cooling import (
    SplitSystem,
    PackagedRTU,
    FanCoilUnit,
    Chiller,
)


# ── Helpers ────────────────────────────────────────────────────────

def _mock_cooling_load(
    peak_total_kw: float,
    peak_sensible_kw: float | None = None,
    peak_latent_kw: float | None = None,
    t_indoor_c: float = 24.0,
):
    """Create a lightweight mock CoolingLoad for equipment sizing tests."""
    if peak_sensible_kw is None:
        peak_sensible_kw = peak_total_kw * 0.78
    if peak_latent_kw is None:
        peak_latent_kw = peak_total_kw - peak_sensible_kw

    shr = peak_sensible_kw / peak_total_kw if peak_total_kw else 1.0

    load = SimpleNamespace(
        peak_total=Q_(peak_total_kw, 'kW'),
        peak_sensible=Q_(peak_sensible_kw, 'kW'),
        peak_latent=Q_(peak_latent_kw, 'kW'),
        sensible_heat_ratio=shr,
        _rooms=[SimpleNamespace(t_indoor=Q_(t_indoor_c, 'degC'))],
    )
    return load


# ═══════════════════════════════════════════════════════════════════
# GROUP A — Supply Airflow
# ═══════════════════════════════════════════════════════════════════


class TestSupplyAirflowCooling:
    """E-A01: Supply airflow from sensible cooling load."""

    def test_e_a01_cooling(self):
        v = supply_airflow_cooling(
            Q_(6310, 'W'), t_room=Q_(24, 'degC'), t_supply=Q_(13, 'degC'),
        )
        # Expected: 6310 / (1.2 * 1006 * 11) = 0.4754 m³/s
        assert abs(v.magnitude - 0.4754) < 0.005

    def test_e_a02_heating(self):
        v = supply_airflow_heating(
            Q_(3610, 'W'), t_room=Q_(21, 'degC'), t_supply=Q_(40, 'degC'),
        )
        # Expected: 3610 / (1.2 * 1006 * 19) = 0.1574 m³/s
        assert abs(v.magnitude - 0.1574) < 0.003

    def test_e_a03_invalid_t_supply(self):
        with pytest.raises(AirflowCalculationError, match='below room temperature'):
            supply_airflow_cooling(
                Q_(5000, 'W'), t_room=Q_(24, 'degC'), t_supply=Q_(24, 'degC'),
            )

    def test_e_a03b_t_supply_above_room(self):
        """T_supply > T_room should also raise."""
        with pytest.raises(AirflowCalculationError):
            supply_airflow_cooling(
                Q_(5000, 'W'), t_room=Q_(24, 'degC'), t_supply=Q_(25, 'degC'),
            )

    def test_default_temperatures(self):
        """Defaults should be 24°C room, 13°C supply."""
        v = supply_airflow_cooling(Q_(6310, 'W'))
        assert abs(v.magnitude - 0.4754) < 0.005

    def test_airflow_from_cooling_load_wrapper(self):
        load = _mock_cooling_load(8.0, 6.31)
        v = airflow_from_cooling_load(load)
        assert v.magnitude > 0


# ═══════════════════════════════════════════════════════════════════
# GROUP B — Cooling Equipment
# ═══════════════════════════════════════════════════════════════════


class TestSplitSystem:
    """E-B01, E-B02: SplitSystem sizing."""

    def test_e_b01_residential_exact(self):
        load = _mock_cooling_load(3.5, 2.73, 0.77)
        ss = SplitSystem(load, cop_rated=3.5)
        assert ss.nominal_capacity.magnitude == 3.5
        assert ss.oversizing_ratio == pytest.approx(1.0, abs=0.001)
        assert ss.input_power_kw.magnitude == pytest.approx(1.0, abs=0.01)
        assert ss.oversizing_warning is None
        assert ss.equipment_subtype == 'residential'

    def test_e_b02_light_commercial(self):
        load = _mock_cooling_load(7.8, 6.1, 1.7)
        ss = SplitSystem(load, cop_rated=3.5)
        assert ss.nominal_capacity.magnitude == 8.0
        assert ss.oversizing_ratio == pytest.approx(1.026, abs=0.01)
        assert ss.oversizing_warning is None
        assert ss.equipment_subtype == 'light_commercial'

    def test_split_multi_split(self):
        load = _mock_cooling_load(15.0)
        ss = SplitSystem(load, multi_split=True)
        n = math.ceil(15.0 / 6.0)
        assert f'{n} indoor' in ss.summary()

    def test_split_summary_format(self):
        load = _mock_cooling_load(3.5)
        ss = SplitSystem(load)
        s = ss.summary()
        assert 'EQUIPMENT SIZING SUMMARY' in s
        assert 'LOAD' in s
        assert 'SELECTED EQUIPMENT' in s
        assert 'AIRFLOW' in s
        assert 'WARNINGS' in s

    def test_split_to_dict(self):
        load = _mock_cooling_load(3.5)
        ss = SplitSystem(load)
        d = ss.to_dict()
        assert 'required_capacity_kw' in d
        assert 'nominal_capacity_kw' in d
        assert 'oversizing_ratio' in d


class TestPackagedRTU:
    """E-B03: PackagedRTU oversizing warning."""

    def test_e_b03_oversizing_warning(self):
        """7.01 kW → next standard size 8.8 kW (ratio 1.255 > 1.25) → WARNING level."""
        # RTU small table: 7.0, 8.8, 10.5, 12.3, 14.1, ...
        # 7.01 required → 8.8 nominal → ratio 8.8/7.01 = 1.255 > 1.25 → WARNING
        load = _mock_cooling_load(7.01, 5.5, 1.51)
        rtu = PackagedRTU(load, cop_rated=3.2)
        assert rtu.nominal_capacity.magnitude == 8.8
        assert rtu.oversizing_ratio > 1.25
        assert rtu.oversizing_warning == 'WARNING'

    def test_rtu_eer(self):
        load = _mock_cooling_load(10.0)
        rtu = PackagedRTU(load, cop_rated=3.2)
        assert rtu.eer == pytest.approx(3.2 * 3.412, abs=0.01)

    def test_rtu_economiser_label(self):
        load = _mock_cooling_load(10.0)
        rtu = PackagedRTU(load, has_economiser=True)
        assert 'Economiser' in rtu.summary()

    def test_rtu_critical_oversizing(self):
        """Test critical oversizing flag (>1.50)."""
        load = _mock_cooling_load(4.5, 3.5, 1.0)
        rtu = PackagedRTU(load, cop_rated=3.2)
        # 4.5kW → packaged_rtu_small → 7.0kW → ratio=1.556
        assert rtu.oversizing_warning == 'CRITICAL'


class TestFanCoilUnit:
    """E-B04: FanCoilUnit CHW flow."""

    def test_e_b04_chw_flow(self):
        load = _mock_cooling_load(5.3, 4.13, 1.17)
        fcu = FanCoilUnit(
            load,
            chilled_water_supply_t=Q_(7, 'degC'),
            chilled_water_return_t=Q_(12, 'degC'),
        )
        assert fcu.nominal_capacity.magnitude == 5.3
        # m_dot = 5300 / (4186 * 5) = 0.2533 kg/s → 0.253 L/s
        assert abs(fcu.chw_flow_rate.magnitude - 0.253) < 0.005

    def test_fcu_delta_t(self):
        load = _mock_cooling_load(3.5)
        fcu = FanCoilUnit(load)
        assert fcu.delta_t_chw.magnitude == pytest.approx(5.0, abs=0.1)

    def test_fcu_default_chw_temps(self):
        load = _mock_cooling_load(3.5)
        fcu = FanCoilUnit(load)
        # Default: 7°C supply, 12°C return → ΔT=5K
        assert fcu.delta_t_chw.magnitude == pytest.approx(5.0, abs=0.1)


class TestChiller:
    """E-B05, E-B06, E-B07: Chiller sizing."""

    def test_e_b05_condenser_rejection(self):
        """100 kW → water-cooled table starts at 175 kW; condenser rejection = 100*(1+1/5.5) = 118.2 kW."""
        load = _mock_cooling_load(100.0, 78.0, 22.0)
        ch = Chiller(load, chiller_type='water_cooled', cop_rated=5.5)
        assert ch.nominal_capacity.magnitude == pytest.approx(175.0, abs=1.0)
        # Q_cond = Q_total * (1 + 1/COP) = 100 * (1 + 1/5.5) = 118.2 kW
        assert ch.condenser_heat_rejection.magnitude == pytest.approx(118.2, abs=0.1)
        # tower flow = Q_cond / (CP_water * ΔT_tower * rho) = 118200 / (4186 * 5) = 5.65 L/s
        assert ch.cooling_tower_flow is not None
        assert abs(ch.cooling_tower_flow.magnitude - 5.65) < 0.1

    def test_e_b06_n_plus_1(self):
        load = _mock_cooling_load(200.0, 156.0, 44.0)
        ch = Chiller(
            load, n_units=3, redundancy='n+1', chiller_type='air_cooled',
        )
        # Size per unit: 200/2 = 100 kW → next_size_up = 105 kW
        assert ch.capacity_per_unit.magnitude == 105.0

    def test_e_b07_exceeds_max(self):
        load = _mock_cooling_load(3000.0)
        with pytest.raises(EquipmentSizingError):
            Chiller(load, chiller_type='water_cooled', n_units=1)

    def test_chiller_air_cooled_no_tower(self):
        load = _mock_cooling_load(50.0)
        ch = Chiller(load, chiller_type='air_cooled')
        assert ch.cooling_tower_flow is None

    def test_chiller_n_plus_1_requires_min_2(self):
        load = _mock_cooling_load(50.0)
        with pytest.raises(EquipmentSizingError, match='n_units >= 2'):
            Chiller(load, n_units=1, redundancy='n+1')

    def test_chiller_default_cop(self):
        load = _mock_cooling_load(50.0)
        ch_air = Chiller(load, chiller_type='air_cooled')
        ch_water = Chiller(load, chiller_type='water_cooled')
        assert ch_air._cop_rated == 3.2
        assert ch_water._cop_rated == 5.5
