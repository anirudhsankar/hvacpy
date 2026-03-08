"""Tests for air-source heat pump sizing — v0.4.

Test group C from the spec.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from hvacpy.units import Q_
from hvacpy.equipment._heatpump import (
    AirSourceHeatPump,
    _cop_correction_cooling,
    _cop_correction_heating,
    _heating_capacity_at_temp,
)


# ── Helpers ────────────────────────────────────────────────────────

def _mock_cooling_load(peak_total_kw, peak_sensible_kw=None, t_indoor_c=24.0):
    if peak_sensible_kw is None:
        peak_sensible_kw = peak_total_kw * 0.78
    peak_latent_kw = peak_total_kw - peak_sensible_kw
    shr = peak_sensible_kw / peak_total_kw if peak_total_kw else 1.0
    return SimpleNamespace(
        peak_total=Q_(peak_total_kw, 'kW'),
        peak_sensible=Q_(peak_sensible_kw, 'kW'),
        peak_latent=Q_(peak_latent_kw, 'kW'),
        sensible_heat_ratio=shr,
        _rooms=[SimpleNamespace(t_indoor=Q_(t_indoor_c, 'degC'))],
    )


def _mock_heating_load(total_kw):
    return SimpleNamespace(total=Q_(total_kw, 'kW'))


# ═══════════════════════════════════════════════════════════════════
# GROUP C — Heat Pump
# ═══════════════════════════════════════════════════════════════════


class TestCOPCorrections:
    """E-C03, E-C04: COP correction functions."""

    def test_e_c03_cooling_43c(self):
        cop = _cop_correction_cooling(3.5, 43.0)
        # COP = 3.5 * (1 - 0.013 * 8) = 3.5 * 0.896 = 3.136
        assert abs(cop - 3.136) < 0.01

    def test_e_c04_heating_neg10c(self):
        cop = _cop_correction_heating(3.8, -10.0)
        # COP = 3.8 * (1 + 0.025 * (-18.3)) = 3.8 * 0.5425 = 2.062
        assert abs(cop - 2.062) < 0.01

    def test_cooling_cop_at_35c(self):
        """At rated conditions, COP should equal rated COP."""
        cop = _cop_correction_cooling(3.5, 35.0)
        assert cop == pytest.approx(3.5, abs=0.001)

    def test_heating_cop_at_8_3c(self):
        """At rated conditions, COP should equal rated COP."""
        cop = _cop_correction_heating(3.8, 8.3)
        assert cop == pytest.approx(3.8, abs=0.001)

    def test_cooling_cop_minimum(self):
        """COP should not drop below 1.5."""
        cop = _cop_correction_cooling(2.0, 100.0)
        assert cop >= 1.5

    def test_heating_cop_minimum(self):
        """COP should not drop below 1.0."""
        cop = _cop_correction_heating(2.0, -100.0)
        assert cop >= 1.0


class TestHeatingCapacity:
    """Heating capacity derating."""

    def test_heating_capacity_at_rated(self):
        # At 8.3°C: Q_heat = nominal * 1.15 * (1 + 0) = nominal * 1.15
        q = _heating_capacity_at_temp(10.0, 8.3)
        assert q == pytest.approx(11.5, abs=0.01)

    def test_heating_capacity_minimum_clamp(self):
        """Should not go below 0.5 * nominal."""
        q = _heating_capacity_at_temp(10.0, -100.0)
        assert q >= 5.0  # 0.5 * 10


class TestAirSourceHeatPump:
    """E-C01, E-C02: Heat pump sizing."""

    def test_e_c01_cooling_binding(self):
        cl = _mock_cooling_load(8.0)
        hl = _mock_heating_load(3.0)
        hp = AirSourceHeatPump(
            cl, hl,
            t_outdoor_cooling=Q_(35, 'degC'),
            t_outdoor_heating=Q_(-3, 'degC'),
        )
        assert hp.nominal_capacity_kw.magnitude == 8.8
        assert hp.binding_mode == 'cooling'
        assert hp.needs_supplemental_heat is False

    def test_e_c02_supplemental_needed(self):
        cl = _mock_cooling_load(5.0)
        hl = _mock_heating_load(12.0)
        hp = AirSourceHeatPump(
            cl, hl,
            t_outdoor_heating=Q_(-15, 'degC'),
        )
        assert hp.needs_supplemental_heat is True
        assert hp.supplemental_heat_kw.magnitude > 0

    def test_hp_coverage_property(self):
        cl = _mock_cooling_load(5.0)
        hl = _mock_heating_load(3.0)
        hp = AirSourceHeatPump(cl, hl)
        assert hp.heating_coverage > 0

    def test_hp_cop_at_design(self):
        cl = _mock_cooling_load(5.0)
        hl = _mock_heating_load(3.0)
        hp = AirSourceHeatPump(
            cl, hl,
            t_outdoor_cooling=Q_(35, 'degC'),
            t_outdoor_heating=Q_(8.3, 'degC'),
        )
        assert hp.cop_at_design_cooling == pytest.approx(3.5, abs=0.01)
        assert hp.cop_at_design_heating == pytest.approx(3.8, abs=0.01)

    def test_hp_summary_format(self):
        cl = _mock_cooling_load(5.0)
        hl = _mock_heating_load(3.0)
        hp = AirSourceHeatPump(cl, hl)
        s = hp.summary()
        assert 'HEAT PUMP SIZING SUMMARY' in s
        assert 'COOLING MODE' in s
        assert 'HEATING MODE' in s
        assert 'BINDING MODE' in s

    def test_hp_no_supplemental_returns_zero(self):
        cl = _mock_cooling_load(10.0)
        hl = _mock_heating_load(3.0)
        hp = AirSourceHeatPump(cl, hl)
        assert hp.supplemental_heat_kw.magnitude == 0

    def test_hp_cooling_oversizing(self):
        cl = _mock_cooling_load(5.0)
        hl = _mock_heating_load(3.0)
        hp = AirSourceHeatPump(cl, hl)
        assert hp.cooling_oversizing >= 1.0

    def test_hp_supply_airflow(self):
        cl = _mock_cooling_load(5.0)
        hl = _mock_heating_load(3.0)
        hp = AirSourceHeatPump(cl, hl)
        assert hp.supply_airflow.magnitude > 0
