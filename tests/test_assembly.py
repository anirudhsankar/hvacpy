"""Unit tests for hvacpy/assembly.py — Tests A-01 through A-12."""

import pytest

from hvacpy import Q_, db, Assembly
from hvacpy.exceptions import UnitError


class TestSingleLayerAssembly:
    """TEST A-01 — single layer dense concrete wall."""

    def test_a01_single_layer_concrete(self) -> None:
        """A-01: 200mm dense concrete wall, orientation=wall."""
        wall = Assembly("Test").add_layer("concrete_dense", Q_(200, "mm"))
        # R = 0.13 + (0.200/1.75) + 0.04 = 0.284
        assert abs(wall.r_value.magnitude - 0.284) < 0.001
        # U = 1 / 0.284 = 3.521
        assert abs(wall.u_value.magnitude - 3.521) < 0.01


class TestCavityWall:
    """TEST A-02 — classic UK cavity wall."""

    def test_a02_cavity_wall(self) -> None:
        """A-02: 4-layer cavity wall, orientation=wall."""
        wall = Assembly("Cavity Wall")
        wall.add_layer("brick_common", Q_(102.5, "mm"))
        wall.add_layer("air_cavity_50mm", Q_(50, "mm"))
        wall.add_layer("mineral_wool_batt", Q_(75, "mm"))
        wall.add_layer("plasterboard_std", Q_(12.5, "mm"))
        # R_total = 0.13 + 4.077 + 0.04 = 4.247
        assert abs(wall.r_value.magnitude - 4.247) < 0.002
        # U = 0.235
        assert abs(wall.u_value.magnitude - 0.235) < 0.001


class TestFlatRoof:
    """TEST A-03 — flat roof with orientation='roof'."""

    def test_a03_flat_roof(self) -> None:
        """A-03: 3-layer flat roof, orientation=roof."""
        roof = Assembly("Flat Roof", orientation="roof")
        roof.add_layer("concrete_dense", Q_(150, "mm"))
        roof.add_layer("xps_insulation", Q_(100, "mm"))
        roof.add_layer("bitumen_felt", Q_(5, "mm"))
        # R_total = 0.10 + 3.555 + 0.04 = 3.695
        assert abs(roof.r_value.magnitude - 3.695) < 0.002
        # U = 0.271
        assert abs(roof.u_value.magnitude - 0.271) < 0.001


class TestFloorSlab:
    """TEST A-04 — floor slab with orientation='floor'."""

    def test_a04_floor_slab(self) -> None:
        """A-04: 3-layer floor slab, orientation=floor."""
        floor = Assembly("Floor Slab", orientation="floor")
        floor.add_layer("concrete_dense", Q_(100, "mm"))
        floor.add_layer("eps_insulation", Q_(50, "mm"))
        floor.add_layer("screed_sand_cement", Q_(65, "mm"))
        # R_total = 0.17 + 1.731 + 0.04 = 1.941
        assert abs(floor.r_value.magnitude - 1.941) < 0.002
        # U = 0.515
        assert abs(floor.u_value.magnitude - 0.515) < 0.002


class TestHighPerformanceWall:
    """TEST A-05 — high performance wall, low U target."""

    def test_a05_high_performance_wall(self) -> None:
        """A-05: 4-layer high performance wall."""
        wall = Assembly("HP Wall")
        wall.add_layer("brick_face", Q_(100, "mm"))
        wall.add_layer("mineral_wool_board", Q_(200, "mm"))
        wall.add_layer("concrete_block_200", Q_(200, "mm"))
        wall.add_layer("plasterboard_std", Q_(12.5, "mm"))
        # R_total = 0.13 + 6.084 + 0.04 = 6.254
        assert abs(wall.r_value.magnitude - 6.254) < 0.002
        # U = 0.160
        assert abs(wall.u_value.magnitude - 0.160) < 0.001


class TestChaining:
    """TEST A-06 — chained add_layer calls."""

    def test_a06_chained_add_layer(self) -> None:
        """A-06: Method chaining works and produces correct state."""
        wall = (
            Assembly("Chain Test")
            .add_layer("brick_common", Q_(110, "mm"))
            .add_layer("mineral_wool_batt", Q_(100, "mm"))
        )
        assert len(wall.layers) == 2
        # r_value should be a Quantity with m²·K/W units.
        assert "kelvin * meter ** 2" in str(wall.r_value.units) or \
            "K" in str(wall.r_value.units)


class TestMaterialObject:
    """TEST A-07 — Material passed as object, not string."""

    def test_a07_material_as_object(self) -> None:
        """A-07: Passing Material object gives same R as string key."""
        mat = db.get("brick_common")

        wall_str = Assembly("Test Str").add_layer(
            "brick_common", Q_(110, "mm")
        )
        wall_obj = Assembly("Test Obj").add_layer(
            mat, Q_(110, "mm")
        )

        assert abs(
            wall_str.r_value.magnitude - wall_obj.r_value.magnitude
        ) < 0.001

        # Key should be None when Material object is passed.
        assert wall_obj.layers[0]["key"] is None


class TestEmptyAssembly:
    """TEST A-08 — zero-layer assembly."""

    def test_a08_empty_assembly(self) -> None:
        """A-08: Surface resistances only."""
        wall = Assembly("Empty")
        # R = 0.13 + 0.04 = 0.170
        assert abs(wall.r_value.magnitude - 0.170) < 0.001
        # U = 1/0.170 = 5.882
        assert abs(wall.u_value.magnitude - 5.882) < 0.001


class TestImperialInput:
    """TEST A-09 — imperial thickness input."""

    def test_a09_imperial_thickness(self) -> None:
        """A-09: 4.33 inch gives same R as ~110 mm."""
        wall_imperial = Assembly("Imperial").add_layer(
            "brick_common", Q_(4.33, "inch")
        )
        wall_metric = Assembly("Metric").add_layer(
            "brick_common", Q_(110, "mm")
        )
        assert abs(
            wall_imperial.r_value.magnitude
            - wall_metric.r_value.magnitude
        ) < 0.001


class TestInvalidInputs:
    """TEST A-10 and A-11 — invalid thickness inputs."""

    def test_a10_zero_thickness(self) -> None:
        """A-10: Zero thickness raises ValueError."""
        with pytest.raises(ValueError, match="positive"):
            Assembly("Test").add_layer("brick_common", Q_(0, "mm"))

    def test_a11_wrong_unit(self) -> None:
        """A-11: Non-length unit raises UnitError."""
        with pytest.raises(UnitError):
            Assembly("Test").add_layer("brick_common", Q_(110, "kg"))

    def test_negative_thickness(self) -> None:
        """Negative thickness raises ValueError."""
        with pytest.raises(ValueError, match="positive"):
            Assembly("Test").add_layer(
                "brick_common", Q_(-110, "mm")
            )

    def test_string_thickness_raises_type_error(self) -> None:
        """String thickness raises TypeError."""
        with pytest.raises(TypeError, match="pint Quantity"):
            Assembly("Test").add_layer(
                "brick_common", "110mm"  # type: ignore
            )

    def test_invalid_orientation(self) -> None:
        """Invalid orientation raises ValueError."""
        with pytest.raises(ValueError, match="orientation"):
            Assembly("Test", orientation="ceiling")


class TestRFraction:
    """TEST A-12 — r_fraction sums to 1.0."""

    def test_a12_r_fraction_sums_to_one(self) -> None:
        """A-12: r_fraction across all layers sums to 1.0."""
        wall = Assembly("Fraction Test")
        wall.add_layer("brick_common", Q_(102.5, "mm"))
        wall.add_layer("air_cavity_50mm", Q_(50, "mm"))
        wall.add_layer("mineral_wool_batt", Q_(75, "mm"))
        wall.add_layer("plasterboard_std", Q_(12.5, "mm"))

        total_fraction = sum(
            layer["r_fraction"] for layer in wall.layers
        )
        assert abs(total_fraction - 1.0) < 1e-10


class TestQuickstartExample:
    """Verify the quickstart example from Section 6.

    SPEC CONCERN: Section 6 states U=0.298 W/(m²·K) and R=3.354 m²·K/W
    for brick_common(110mm) + mineral_wool_batt(100mm) +
    plasterboard_std(12.5mm). However, the correct values from the
    series resistance formula with the Section 4.3 material data are:
      R = 0.13 + 0.110/0.72 + 0.100/0.040 + 0.0125/0.21 + 0.04
        = 0.13 + 0.1528 + 2.500 + 0.0595 + 0.04 = 2.882 m²K/W
      U = 1/2.882 = 0.347 W/(m²K)
    The Section 7 test cases (A-01 through A-12) are independently
    verified and all pass. This test uses the physically correct values.
    """

    def test_quickstart_values(self) -> None:
        """Quickstart: verify wall assembly calculation is correct."""
        wall = Assembly("My Wall")
        wall.add_layer("brick_common", Q_(110, "mm"))
        wall.add_layer("mineral_wool_batt", Q_(100, "mm"))
        wall.add_layer("plasterboard_std", Q_(12.5, "mm"))

        # Correct values from the physics:
        # R = 0.13 + 0.1528 + 2.500 + 0.0595 + 0.04 = 2.882
        assert abs(wall.r_value.magnitude - 2.882) < 0.001
        # U = 1/2.882 = 0.347
        assert abs(wall.u_value.magnitude - 0.347) < 0.001


class TestBreakdown:
    """Verify breakdown() produces output without errors."""

    def test_breakdown_output(self) -> None:
        """breakdown() returns a non-empty string with key info."""
        wall = Assembly("Brick Cavity Wall")
        wall.add_layer("brick_common", Q_(110, "mm"))
        wall.add_layer("air_cavity_50mm", Q_(50, "mm"))
        wall.add_layer("mineral_wool_batt", Q_(75, "mm"))
        wall.add_layer("plasterboard_std", Q_(12.5, "mm"))

        output = wall.breakdown()
        assert isinstance(output, str)
        assert "Brick Cavity Wall" in output
        assert "R_total" in output
        assert "U_value" in output
        assert "R_se" in output
        assert "R_si" in output
