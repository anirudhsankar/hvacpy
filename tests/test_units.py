"""Unit tests for hvacpy/units.py — Tests U-01 through U-04."""

import pytest

from hvacpy import Q_, validate_unit
from hvacpy.exceptions import UnitError


class TestUnitConversions:
    """TEST U-01 and U-02 — unit conversions."""

    def test_u01_thickness_mm_to_m(self) -> None:
        """U-01: 110 mm converts to 0.11 m."""
        result = Q_(110, "mm").to("m")
        assert abs(result.magnitude - 0.11) < 1e-10

    def test_u02_imperial_r_to_si_r(self) -> None:
        """U-02: 19 ft²·°F·h/BTU converts to ~3.346 m²·K/W."""
        imperial_r = Q_(19, "ft**2 * degF * hr / BTU")
        si_r = imperial_r.to("m**2 * K / W")
        assert abs(si_r.magnitude - 3.346) < 0.001


class TestValidateUnit:
    """TEST U-03 and U-04 — validate_unit function."""

    def test_u03_correct_dimensionality_passes(self) -> None:
        """U-03: validate_unit does not raise for correct dims."""
        # Conductivity: W/(m·K) has dimensionality
        # [length] * [mass] / [time]³ / [temperature]
        validate_unit(
            Q_(0.5, "W/(m*K)"),
            "[length] * [mass] / [time] ** 3 / [temperature]",
            "conductivity",
        )
        # If no exception, the test passes.

    def test_u04_wrong_dimensionality_raises(self) -> None:
        """U-04: validate_unit raises UnitError for wrong dims."""
        with pytest.raises(UnitError, match="conductivity"):
            validate_unit(
                Q_(0.5, "m"),
                "[length] * [mass] / [time] ** 3 / [temperature]",
                "conductivity",
            )
