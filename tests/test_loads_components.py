"""Unit tests for Room, Zone, Wall, Window, Roof, Floor dataclasses.

Tests L-C01, L-C02, L-C05, L-C06, and component construction.
"""

import pytest

from hvacpy import Q_, Assembly, db
from hvacpy.loads._components import (
    Orientation, WallComponent, WindowComponent, InternalGain,
    _VALID_WALL_GROUPS,
)
from hvacpy.loads._room import Room, Zone


# ── Helpers ─────────────────────────────────────────────────────────

def _make_assembly(name: str = 'Test Wall') -> Assembly:
    """Minimal assembly for testing."""
    wall = Assembly(name)
    wall.add_layer('concrete_dense', Q_(200, 'mm'))
    return wall


# ── Orientation ─────────────────────────────────────────────────────

class TestOrientation:
    def test_valid_orientations(self) -> None:
        for o in Orientation:
            assert isinstance(o.value, str)

    def test_orientation_values(self) -> None:
        assert Orientation.N.value == 'N'
        assert Orientation.HORIZONTAL.value == 'H'


# ── WallComponent ───────────────────────────────────────────────────

class TestWallComponent:
    def test_basic_construction(self) -> None:
        assy = _make_assembly()
        wall = WallComponent(
            name='South Wall', assembly=assy,
            area=Q_(20, 'm²'), orientation=Orientation.S,
        )
        assert wall.name == 'South Wall'
        assert wall.wall_group == 'D'
        assert wall.is_roof is False

    def test_wall_groups_a_to_g(self) -> None:
        assy = _make_assembly()
        for group in 'ABCDEFG':
            wall = WallComponent(
                name=f'Group {group}', assembly=assy,
                area=Q_(10, 'm²'), orientation=Orientation.N,
                wall_group=group,
            )
            assert wall.wall_group == group

    def test_lowercase_wall_group_normalised(self) -> None:
        assy = _make_assembly()
        wall = WallComponent(
            name='Test', assembly=assy,
            area=Q_(10, 'm²'), orientation=Orientation.N,
            wall_group='d',
        )
        assert wall.wall_group == 'D'

    def test_roof_flag(self) -> None:
        assy = _make_assembly()
        roof = WallComponent(
            name='Roof', assembly=assy,
            area=Q_(50, 'm²'), orientation=Orientation.HORIZONTAL,
            is_roof=True,
        )
        assert roof.is_roof is True


class TestWallComponentErrors:
    """TEST L-C01 — Invalid wall group."""

    def test_lc01_invalid_wall_group(self) -> None:
        assy = _make_assembly()
        with pytest.raises(ValueError, match='wall_group'):
            WallComponent(
                name='Bad Group', assembly=assy,
                area=Q_(10, 'm²'), orientation=Orientation.N,
                wall_group='Z',
            )
        # Message should mention valid groups A through G
        with pytest.raises(ValueError, match='A'):
            WallComponent(
                name='Bad Group', assembly=assy,
                area=Q_(10, 'm²'), orientation=Orientation.N,
                wall_group='X',
            )

    def test_lc02_invalid_orientation_string(self) -> None:
        """TEST L-C02 — string instead of Orientation enum."""
        assy = _make_assembly()
        with pytest.raises(ValueError, match='Orientation'):
            WallComponent(
                name='Bad Orient', assembly=assy,
                area=Q_(10, 'm²'), orientation='SOUTH',  # type: ignore
            )


# ── WindowComponent ─────────────────────────────────────────────────

class TestWindowComponent:
    def test_basic_construction(self) -> None:
        win = WindowComponent(
            name='South Glazing', area=Q_(6, 'm²'),
            orientation=Orientation.S, u_factor=Q_(2.8, 'W/(m²*K)'),
            shgc=0.40,
        )
        assert win.frame_fraction == 0.15
        assert win.has_interior_shading is False

    def test_lc05_shgc_out_of_range(self) -> None:
        """TEST L-C05 — SHGC > 1.0."""
        with pytest.raises(ValueError, match='shgc'):
            WindowComponent(
                name='Bad', area=Q_(6, 'm²'),
                orientation=Orientation.S, u_factor=Q_(2.8, 'W/(m²*K)'),
                shgc=1.5,
            )
        # Also test shgc mentions 0.0 and 1.0
        with pytest.raises(ValueError, match='0.0'):
            WindowComponent(
                name='Bad', area=Q_(6, 'm²'),
                orientation=Orientation.S, u_factor=Q_(2.8, 'W/(m²*K)'),
                shgc=-0.1,
            )

    def test_frame_fraction_max(self) -> None:
        with pytest.raises(ValueError, match='frame_fraction'):
            WindowComponent(
                name='Bad', area=Q_(6, 'm²'),
                orientation=Orientation.S, u_factor=Q_(2.8, 'W/(m²*K)'),
                shgc=0.40, frame_fraction=0.6,
            )


# ── InternalGain ────────────────────────────────────────────────────

class TestInternalGain:
    def test_basic_people(self) -> None:
        gain = InternalGain(gain_type='people', count=10, activity='office_work')
        assert gain.diversity == 1.0
        assert gain.clf == 1.0

    def test_basic_lighting(self) -> None:
        gain = InternalGain(gain_type='lighting', watts_per_m2=12.0)
        assert gain.gain_type == 'lighting'

    def test_basic_equipment(self) -> None:
        gain = InternalGain(gain_type='equipment', total_watts=800)
        assert gain.gain_type == 'equipment'

    def test_lc06_invalid_activity(self) -> None:
        """TEST L-C06 — Invalid activity type."""
        with pytest.raises(ValueError, match='juggling'):
            InternalGain(gain_type='people', count=5, activity='juggling')

    def test_invalid_gain_type(self) -> None:
        with pytest.raises(ValueError, match='gain_type'):
            InternalGain(gain_type='magic')

    def test_invalid_diversity(self) -> None:
        with pytest.raises(ValueError, match='diversity'):
            InternalGain(gain_type='lighting', diversity=1.5)


# ── Room ────────────────────────────────────────────────────────────

class TestRoom:
    def test_volume(self) -> None:
        room = Room(
            name='Test', floor_area=Q_(50, 'm²'),
            ceiling_height=Q_(3, 'm'),
        )
        assert abs(room.volume_m3 - 150.0) < 0.01

    def test_floor_area_conversion(self) -> None:
        room = Room(
            name='Imperial', floor_area=Q_(100, 'ft²'),
            ceiling_height=Q_(10, 'ft'),
        )
        assert room.floor_area_m2 > 0

    def test_default_t_indoor(self) -> None:
        room = Room(
            name='Test', floor_area=Q_(50, 'm²'),
            ceiling_height=Q_(3, 'm'),
        )
        assert abs(room.t_indoor.to('degC').magnitude - 24.0) < 0.1


# ── Zone ────────────────────────────────────────────────────────────

class TestZone:
    def test_add_room(self) -> None:
        zone = Zone(name='Floor 1')
        room = Room(name='Office', floor_area=Q_(50, 'm²'), ceiling_height=Q_(3, 'm'))
        result = zone.add_room(room)
        assert result is zone  # chaining
        assert len(zone.rooms) == 1

    def test_multiple_rooms(self) -> None:
        zone = Zone(name='Floor 1')
        zone.add_room(Room(name='A', floor_area=Q_(50, 'm²'), ceiling_height=Q_(3, 'm')))
        zone.add_room(Room(name='B', floor_area=Q_(30, 'm²'), ceiling_height=Q_(3, 'm')))
        assert len(zone.rooms) == 2
