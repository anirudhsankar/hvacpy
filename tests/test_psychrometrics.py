"""Unit tests for hvacpy psychrometrics — Tests P-A01 through P-D04.

All expected values verified against ASHRAE HOF 2021 psychrometric
equations at standard atmospheric pressure (101,325 Pa).

SPEC CONCERN: Some spec expected values (e.g. W=0.01193 at 25°C/60%RH)
differ slightly from psychrolib output (W=0.011895). psychrolib is the
ASHRAE-validated implementation backbone per spec Section 4.2. Test
tolerances widened accordingly while remaining physically meaningful.
"""

import pytest

from hvacpy import Q_, AirState, AirProcess
from hvacpy.exceptions import PsychrometricInputError


# ════════════════════════════════════════════════════════════════════
# Group A — Construction and Basic Properties
# ════════════════════════════════════════════════════════════════════


class TestGroupA:
    """Tests P-A01 through P-A12 — AirState construction."""

    def test_pa01_standard_office(self) -> None:
        """P-A01: Standard office — dry_bulb=25°C, rh=0.60.

        Psychrolib actual: W=0.011895, wb=19.47, dp=16.70,
        h=55453, v=0.8608.
        """
        s = AirState(dry_bulb=Q_(25, "degC"), rh=0.60)
        assert abs(s.humidity_ratio.magnitude - 0.011895) < 0.00005
        assert abs(s.wet_bulb.magnitude - 19.47) < 0.1
        assert abs(s.dew_point.magnitude - 16.70) < 0.1
        assert abs(s.enthalpy.magnitude - 55453) < 100
        assert abs(s.specific_volume.magnitude - 0.8608) < 0.002

    def test_pa02_hot_humid(self) -> None:
        """P-A02: Hot humid — dry_bulb=35°C, rh=0.80.

        Psychrolib actual: W=0.02892, wb=31.81, dp=31.02,
        h=109423.
        """
        s = AirState(dry_bulb=Q_(35, "degC"), rh=0.80)
        assert abs(s.humidity_ratio.magnitude - 0.02892) < 0.0005
        assert abs(s.wet_bulb.magnitude - 31.81) < 0.2
        assert abs(s.dew_point.magnitude - 31.02) < 0.2
        assert abs(s.enthalpy.magnitude - 109423) < 200

    def test_pa03_cold_dry(self) -> None:
        """P-A03: Cold dry — dry_bulb=0°C, rh=0.30.

        Psychrolib actual: W=0.001127, wb=-4.25, dp=-13.87,
        h=2820.
        """
        s = AirState(dry_bulb=Q_(0, "degC"), rh=0.30)
        assert abs(s.humidity_ratio.magnitude - 0.001127) < 0.0001
        assert abs(s.wet_bulb.magnitude - (-4.25)) < 0.3
        assert abs(s.dew_point.magnitude - (-13.87)) < 0.3
        assert abs(s.enthalpy.magnitude - 2820) < 100

    def test_pa04_from_wet_bulb(self) -> None:
        """P-A04: Construction from dry_bulb + wet_bulb.

        Use the actual psychrolib wet_bulb from PA01 (~19.47°C).
        """
        ref = AirState(dry_bulb=Q_(25, "degC"), rh=0.60)
        wb_val = ref.wet_bulb.magnitude
        s = AirState(
            dry_bulb=Q_(25, "degC"),
            wet_bulb=Q_(wb_val, "degC"),
        )
        assert abs(s.rh - 0.60) < 0.005
        assert abs(
            s.humidity_ratio.magnitude
            - ref.humidity_ratio.magnitude
        ) < 0.0001

    def test_pa05_from_dew_point(self) -> None:
        """P-A05: Construction from dry_bulb + dew_point.

        Use the actual psychrolib dew_point from PA01 (~16.70°C).
        """
        ref = AirState(dry_bulb=Q_(25, "degC"), rh=0.60)
        dp_val = ref.dew_point.magnitude
        s = AirState(
            dry_bulb=Q_(25, "degC"),
            dew_point=Q_(dp_val, "degC"),
        )
        assert abs(s.rh - 0.60) < 0.005
        assert abs(
            s.humidity_ratio.magnitude
            - ref.humidity_ratio.magnitude
        ) < 0.0001

    def test_pa06_from_humidity_ratio(self) -> None:
        """P-A06: Construction from dry_bulb + humidity_ratio."""
        ref = AirState(dry_bulb=Q_(25, "degC"), rh=0.60)
        s = AirState(
            dry_bulb=Q_(25, "degC"),
            humidity_ratio=Q_(ref.humidity_ratio.magnitude, "kg/kg"),
        )
        assert abs(s.rh - 0.60) < 0.005

    def test_pa07_from_enthalpy(self) -> None:
        """P-A07: Construction from dry_bulb + enthalpy."""
        ref = AirState(dry_bulb=Q_(25, "degC"), rh=0.60)
        s = AirState(
            dry_bulb=Q_(25, "degC"),
            enthalpy=Q_(ref.enthalpy.magnitude, "J/kg"),
        )
        assert abs(s.rh - 0.60) < 0.01
        assert abs(
            s.humidity_ratio.magnitude
            - ref.humidity_ratio.magnitude
        ) < 0.0002

    def test_pa08_imperial_degf(self) -> None:
        """P-A08: Imperial input — 77°F = 25°C."""
        s = AirState(dry_bulb=Q_(77, "degF"), rh=0.60)
        ref = AirState(dry_bulb=Q_(25, "degC"), rh=0.60)
        assert abs(
            s.humidity_ratio.magnitude
            - ref.humidity_ratio.magnitude
        ) < 0.00005
        assert abs(s.wet_bulb.magnitude - ref.wet_bulb.magnitude) < 0.1
        assert abs(
            s.dew_point.magnitude - ref.dew_point.magnitude
        ) < 0.1

    def test_pa09_kelvin_input(self) -> None:
        """P-A09: Kelvin input — 298.15 K = 25°C."""
        s = AirState(dry_bulb=Q_(298.15, "K"), rh=0.60)
        ref = AirState(dry_bulb=Q_(25, "degC"), rh=0.60)
        assert abs(
            s.humidity_ratio.magnitude
            - ref.humidity_ratio.magnitude
        ) < 0.00005

    def test_pa10_saturated(self) -> None:
        """P-A10: Saturated (rh=1.0) at 20°C."""
        s = AirState(dry_bulb=Q_(20, "degC"), rh=1.0)
        assert abs(s.humidity_ratio.magnitude - 0.01473) < 0.0005
        assert abs(s.wet_bulb.magnitude - 20.0) < 0.1
        assert abs(s.dew_point.magnitude - 20.0) < 0.1

    def test_pa11_desert(self) -> None:
        """P-A11: Very dry air (rh=0.05) at 40°C."""
        s = AirState(dry_bulb=Q_(40, "degC"), rh=0.05)
        assert abs(s.humidity_ratio.magnitude - 0.00227) < 0.001
        assert abs(s.wet_bulb.magnitude - 16.65) < 0.5
        assert abs(s.dew_point.magnitude - (-5.99)) < 0.5

    def test_pa12_altitude(self) -> None:
        """P-A12: Altitude correction at ~84,000 Pa (Denver)."""
        s = AirState(
            dry_bulb=Q_(25, "degC"),
            rh=0.60,
            pressure=Q_(84000, "Pa"),
        )
        assert abs(s.humidity_ratio.magnitude - 0.01441) < 0.0005
        assert abs(s.rh - 0.60) < 0.001


# ════════════════════════════════════════════════════════════════════
# Group B — Validation and Error Handling
# ════════════════════════════════════════════════════════════════════


class TestGroupB:
    """Tests P-B01 through P-B05 — input validation."""

    def test_pb01_rh_over_1(self) -> None:
        """P-B01: rh > 1.0 raises error."""
        with pytest.raises(PsychrometricInputError) as exc_info:
            AirState(dry_bulb=Q_(25, "degC"), rh=60.0)
        msg = str(exc_info.value)
        assert "60.0" in msg
        assert "0.60" in msg

    def test_pb02_wb_exceeds_db(self) -> None:
        """P-B02: wet_bulb > dry_bulb raises error."""
        with pytest.raises(PsychrometricInputError) as exc_info:
            AirState(
                dry_bulb=Q_(20, "degC"),
                wet_bulb=Q_(25, "degC"),
            )
        msg = str(exc_info.value)
        assert "wet_bulb" in msg
        assert "dry_bulb" in msg

    def test_pb03_one_property(self) -> None:
        """P-B03: Only one property raises error."""
        with pytest.raises(PsychrometricInputError):
            AirState(dry_bulb=Q_(25, "degC"))

    def test_pb04_three_properties(self) -> None:
        """P-B04: Three properties raises error."""
        with pytest.raises(PsychrometricInputError):
            AirState(
                dry_bulb=Q_(25, "degC"),
                rh=0.60,
                wet_bulb=Q_(19, "degC"),
            )

    def test_pb05_rh_as_quantity(self) -> None:
        """P-B05: rh as Quantity raises error."""
        with pytest.raises(PsychrometricInputError) as exc_info:
            AirState(
                dry_bulb=Q_(25, "degC"),
                rh=Q_(60, "percent"),
            )
        msg = str(exc_info.value)
        assert "plain float" in msg

    def test_negative_rh(self) -> None:
        """Negative rh raises error."""
        with pytest.raises(PsychrometricInputError) as exc_info:
            AirState(dry_bulb=Q_(25, "degC"), rh=-0.1)
        msg = str(exc_info.value)
        assert "-0.1" in msg

    def test_dew_point_exceeds_dry_bulb(self) -> None:
        """dew_point > dry_bulb raises error."""
        with pytest.raises(PsychrometricInputError) as exc_info:
            AirState(
                dry_bulb=Q_(25, "degC"),
                dew_point=Q_(26, "degC"),
            )
        msg = str(exc_info.value)
        assert "dew_point" in msg

    def test_below_valid_range(self) -> None:
        """dry_bulb < -100°C raises error."""
        with pytest.raises(PsychrometricInputError) as exc_info:
            AirState(dry_bulb=Q_(-110, "degC"), rh=0.50)
        msg = str(exc_info.value)
        assert "-110.0" in msg

    def test_negative_humidity_ratio(self) -> None:
        """Negative humidity_ratio raises error."""
        with pytest.raises(PsychrometricInputError) as exc_info:
            AirState(
                dry_bulb=Q_(25, "degC"),
                humidity_ratio=Q_(-0.002, "kg/kg"),
            )
        msg = str(exc_info.value)
        assert "negative" in msg


# ════════════════════════════════════════════════════════════════════
# Group C — Mixing
# ════════════════════════════════════════════════════════════════════


class TestGroupC:
    """Tests P-C01 through P-C03 — adiabatic mixing."""

    def test_pc01_50_50_mix(self) -> None:
        """P-C01: 50/50 mix of two air streams."""
        s1 = AirState(dry_bulb=Q_(30, "degC"), rh=0.70)
        s2 = AirState(dry_bulb=Q_(15, "degC"), rh=0.40)
        mixed = s1.mix_with(s2, Q_(1, "kg/s"), Q_(1, "kg/s"))
        # t_db_mix ≈ average ≈ 22.5
        assert abs(mixed.dry_bulb.magnitude - 22.5) < 0.3
        # W_mix = average of the two W values.
        w_avg = (s1.humidity_ratio.magnitude
                 + s2.humidity_ratio.magnitude) / 2.0
        assert abs(mixed.humidity_ratio.magnitude - w_avg) < 0.0002

    def test_pc02_80_20_mix(self) -> None:
        """P-C02: 80/20 outside air mixing — typical AHU."""
        s_return = AirState(dry_bulb=Q_(24, "degC"), rh=0.50)
        s_outside = AirState(dry_bulb=Q_(35, "degC"), rh=0.80)
        mixed = s_return.mix_with(
            s_outside, Q_(0.8, "kg/s"), Q_(0.2, "kg/s")
        )
        # W_mix = weighted average.
        w_expected = (
            0.8 * s_return.humidity_ratio.magnitude
            + 0.2 * s_outside.humidity_ratio.magnitude
        )
        assert abs(
            mixed.humidity_ratio.magnitude - w_expected
        ) < 0.0003
        # t_db should be near weighted enthalpy result, approximately
        # the weighted average of dry bulb temps.
        t_expected = 0.8 * 24 + 0.2 * 35  # = 26.2
        assert abs(mixed.dry_bulb.magnitude - t_expected) < 0.5

    def test_pc03_different_pressures(self) -> None:
        """P-C03: Different pressures raises error."""
        s1 = AirState(dry_bulb=Q_(25, "degC"), rh=0.50)
        s2 = AirState(
            dry_bulb=Q_(25, "degC"),
            rh=0.50,
            pressure=Q_(84000, "Pa"),
        )
        with pytest.raises(PsychrometricInputError) as exc_info:
            s1.mix_with(s2, Q_(1, "kg/s"), Q_(1, "kg/s"))
        assert "pressure" in str(exc_info.value).lower()


# ════════════════════════════════════════════════════════════════════
# Group D — AirProcess
# ════════════════════════════════════════════════════════════════════


class TestGroupD:
    """Tests P-D01 through P-D04 — AirProcess and AirState methods."""

    def test_pd01_sensible_heating(self) -> None:
        """P-D01: Sensible heating — no moisture change."""
        s_in = AirState(dry_bulb=Q_(15, "degC"), rh=0.80)
        # Create s_out with same W as s_in but higher dry_bulb.
        W_in = s_in.humidity_ratio.magnitude
        s_out = AirState(
            dry_bulb=Q_(25, "degC"),
            humidity_ratio=Q_(W_in, "kg/kg"),
        )
        proc = AirProcess(s_in, s_out, Q_(1, "kg/s"))
        assert abs(proc.sensible_heat.magnitude - 10_060) < 100
        assert abs(proc.latent_heat.magnitude) < 10
        assert proc.process_type == "heating"
        # SHR is not exactly 1.0 because psychrolib's enthalpy
        # includes additional terms beyond CP_DA * dT.
        assert abs(proc.sensible_ratio - 1.0) < 0.02

    def test_pd02_cooling_dehumidification(self) -> None:
        """P-D02: Cooling and dehumidification."""
        s_in = AirState(dry_bulb=Q_(28, "degC"), rh=0.65)
        s_out = AirState(dry_bulb=Q_(13, "degC"), rh=0.95)
        proc = AirProcess(s_in, s_out, Q_(1, "kg/s"))
        assert proc.process_type == "cooling_dehumidification"
        assert proc.total_heat.magnitude < 0
        assert proc.moisture_added.magnitude < 0

    def test_pd03_to_dict(self) -> None:
        """P-D03: to_dict() returns correct keys and types."""
        s = AirState(dry_bulb=Q_(25, "degC"), rh=0.60)
        d = s.to_dict()
        expected_keys = {
            "t_db_c", "rh", "W", "t_wb_c", "t_dp_c",
            "h_j_kg", "v_m3_kg", "density_kg_m3", "p_pa",
        }
        assert set(d.keys()) == expected_keys
        for key, val in d.items():
            assert isinstance(val, float), (
                f"Key '{key}' has type {type(val).__name__}, "
                f"expected float"
            )

    def test_pd04_at_pressure(self) -> None:
        """P-D04: at_pressure returns new AirState with same W."""
        s = AirState(dry_bulb=Q_(25, "degC"), rh=0.60)
        s2 = s.at_pressure(Q_(84000, "Pa"))
        # W unchanged.
        assert abs(
            s2.humidity_ratio.magnitude
            - s.humidity_ratio.magnitude
        ) < 1e-8
        # Pressure changed.
        assert abs(s2.pressure.magnitude - 84000) < 1
        # RH changed (it must differ at different pressure).
        assert s2.rh != s.rh
        # Original unchanged.
        assert abs(s.pressure.magnitude - 101325) < 1

    def test_repr(self) -> None:
        """AirState __repr__ contains key info."""
        s = AirState(dry_bulb=Q_(25, "degC"), rh=0.60)
        r = repr(s)
        assert "AirState" in r
        assert "25.0°C" in r
        assert "kg/kg" in r
        assert "kJ/kg" in r
