"""Heating load test cases from Section 9.

Test L-B02 — Office in Chicago winter.
"""

import pytest

from hvacpy import Q_, Assembly
from hvacpy.loads import (
    HeatingLoad, Room,
    WallComponent, WindowComponent, Orientation,
)


# ── Helpers ─────────────────────────────────────────────────────────

def _simple_assembly(u_target: float) -> Assembly:
    """Create assembly with approximately the given U-value."""
    r_total = 1.0 / u_target
    r_layer = r_total - 0.13 - 0.04
    if r_layer < 0.001:
        r_layer = 0.001
    thickness_m = r_layer * 1.75
    assy = Assembly('Test')
    assy.add_layer('concrete_dense', Q_(thickness_m * 1000, 'mm'))
    return assy


# ── Test Cases ──────────────────────────────────────────────────────

class TestHeatingLoad:
    """TEST L-B02 — Office in Chicago winter."""

    def test_lb02_chicago_heating(self) -> None:
        """L-B02: Same office geometry, Chicago winter.

        T_indoor=21°C (spec default for heating would be the room's value,
        but we override with a custom indoor temp).
        T_outdoor=-16.7°C (Chicago). Wind 6.7 m/s.
        delta_T = 21 - (-16.7) = 37.7 K

        Wall:   U=0.5, A=20m²  => 0.5*20*37.7 = 377.0 W
        Window: U=2.8, A=6m²   => 2.8*6*37.7  = 633.36 W
        Roof:   U=0.35, A=50m² => 0.35*50*37.7 = 659.75 W
        Envelope total ≈ 1670 W

        Infiltration: ACH=0.5, V=150m³, wind=6.7m/s
        ACH_heating = 0.5 * (6.7/6.7)^0.5 = 0.5
        m_dot = 1.2*0.5*150/3600 = 0.025 kg/s
        Q_inf = 0.025 * 1006 * 37.7 = 948 W

        Total ≈ 2618 W
        Tolerance: ±150 W (±6%)
        """
        assy_wall = _simple_assembly(0.5)
        assy_roof = _simple_assembly(0.35)

        room = Room(
            name='Office', floor_area=Q_(50, 'm²'),
            ceiling_height=Q_(3, 'm'), ach_infiltration=0.5,
            t_indoor=Q_(21, 'degC'),
        )
        room.walls.append(WallComponent(
            name='Wall', assembly=assy_wall,
            area=Q_(20, 'm²'), orientation=Orientation.S,
        ))
        room.walls.append(WallComponent(
            name='Roof', assembly=assy_roof,
            area=Q_(50, 'm²'), orientation=Orientation.HORIZONTAL,
            is_roof=True,
        ))
        room.windows.append(WindowComponent(
            name='Window', area=Q_(6, 'm²'),
            orientation=Orientation.S, u_factor=Q_(2.8, 'W/(m²*K)'),
            shgc=0.40,
        ))

        load = HeatingLoad(room, city='chicago')

        # Check delta_t
        assert abs(load.delta_t.magnitude - 37.7) < 0.5

        # Envelope and infiltration should both be positive
        assert load.envelope_loss.magnitude > 0
        assert load.infiltration_loss.magnitude > 0

        # Total within tolerance
        # Use actual U-values from assemblies
        u_wall = assy_wall.u_value.magnitude
        u_roof = assy_roof.u_value.magnitude
        delta_t = 37.7

        expected_wall = u_wall * 20.0 * delta_t
        expected_window = 2.8 * 6.0 * delta_t
        expected_roof = u_roof * 50.0 * delta_t
        expected_env = expected_wall + expected_window + expected_roof

        expected_inf = 1.2 * 0.5 * 150.0 / 3600.0 * 1006.0 * delta_t
        expected_total = expected_env + expected_inf

        assert abs(load.total.magnitude - expected_total) < 150.0

    def test_heating_breakdown(self) -> None:
        assy = _simple_assembly(0.5)
        room = Room(
            name='Test', floor_area=Q_(50, 'm²'),
            ceiling_height=Q_(3, 'm'), ach_infiltration=0.5,
            t_indoor=Q_(21, 'degC'),
        )
        room.walls.append(WallComponent(
            name='Wall', assembly=assy,
            area=Q_(20, 'm²'), orientation=Orientation.S,
        ))

        load = HeatingLoad(room, t_winter_db=Q_(-10, 'degC'))
        output = load.breakdown()

        assert isinstance(output, str)
        assert 'HEATING TOTAL' in output
        assert 'ENVELOPE TOTAL' in output
        assert 'INFILTRATION TOTAL' in output

    def test_heating_city_lookup(self) -> None:
        assy = _simple_assembly(0.5)
        room = Room(
            name='Test', floor_area=Q_(50, 'm²'),
            ceiling_height=Q_(3, 'm'), ach_infiltration=0.5,
        )
        room.walls.append(WallComponent(
            name='Wall', assembly=assy,
            area=Q_(20, 'm²'), orientation=Orientation.S,
        ))

        load = HeatingLoad(room, city='london')
        assert load.total.magnitude > 0
        # London: T_winter = -3.2, T_indoor = 24
        assert load.delta_t.magnitude > 0

    def test_heating_no_conditions(self) -> None:
        """Must provide city or t_winter_db."""
        from hvacpy.exceptions import HvacpyError
        room = Room(
            name='Test', floor_area=Q_(50, 'm²'),
            ceiling_height=Q_(3, 'm'),
        )
        with pytest.raises(HvacpyError):
            HeatingLoad(room)

    def test_heating_custom_wind_speed(self) -> None:
        assy = _simple_assembly(0.5)
        room = Room(
            name='Test', floor_area=Q_(50, 'm²'),
            ceiling_height=Q_(3, 'm'), ach_infiltration=0.5,
        )
        room.walls.append(WallComponent(
            name='Wall', assembly=assy,
            area=Q_(20, 'm²'), orientation=Orientation.S,
        ))

        load_low = HeatingLoad(
            room, t_winter_db=Q_(-10, 'degC'),
            wind_speed=Q_(3, 'm/s'),
        )
        load_high = HeatingLoad(
            room, t_winter_db=Q_(-10, 'degC'),
            wind_speed=Q_(15, 'm/s'),
        )

        # Higher wind = more infiltration = higher total
        assert load_high.infiltration_loss.magnitude > load_low.infiltration_loss.magnitude
