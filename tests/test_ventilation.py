"""Tests for ventilation compliance — v0.4.

Test group E from the spec.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace

import pytest

from hvacpy.units import Q_
from hvacpy.loads._room import Room
from hvacpy.loads._components import InternalGain
from hvacpy.equipment._ventilation import VentilationCheck, VENTILATION_RATES


# ── Helpers ────────────────────────────────────────────────────────

def _make_room(floor_area_m2, people_count, name='TestRoom'):
    """Create a Room with a 'people' InternalGain."""
    room = Room(
        name=name,
        floor_area=Q_(floor_area_m2, 'm**2'),
        ceiling_height=Q_(3, 'm'),
    )
    if people_count > 0:
        room.internal_gains.append(
            InternalGain('people', count=people_count, activity='office_work')
        )
    return room


# ═══════════════════════════════════════════════════════════════════
# GROUP E — Ventilation
# ═══════════════════════════════════════════════════════════════════


class TestVentilationCompliance:
    """E-E01, E-E02, E-E03: ASHRAE 62.1 ventilation compliance."""

    def test_e_e01_office_compliant(self):
        room = _make_room(50, 8)
        vc = VentilationCheck(
            room,
            supply_airflow=Q_(0.475, 'm**3/s'),
            space_type='office',
            oa_fraction=0.15,
        )
        # Vz = 2.5*8 + 0.3*50 = 35 L/s
        assert abs(vc.required_oa_flow.magnitude - 35.0) < 0.5
        # OA = 0.475 * 0.15 * 1000 = 71.25 L/s
        assert vc.compliant is True

    def test_e_e02_classroom_non_compliant(self):
        room = _make_room(60, 30)
        vc = VentilationCheck(
            room,
            supply_airflow=Q_(0.2, 'm**3/s'),
            space_type='classroom',
            oa_fraction=0.15,
        )
        # Vz = 3.8*30 + 0.6*60 = 150 L/s
        assert vc.compliant is False
        # OA = 0.2 * 0.15 * 1000 = 30 L/s → deficit = 120 L/s
        assert abs(vc.deficit.magnitude - 120.0) < 2.0

    def test_e_e03_data_centre(self):
        room = _make_room(200, 2)
        vc = VentilationCheck(
            room,
            supply_airflow=Q_(5.0, 'm**3/s'),
            space_type='data_centre',
            oa_fraction=0.05,
        )
        # Vz = 0*2 + 0.6*200 = 120 L/s
        assert abs(vc.required_oa_flow.magnitude - 120.0) < 0.5
        # OA = 5.0 * 0.05 * 1000 = 250 L/s
        assert vc.compliant is True


class TestVentilationEdgeCases:
    """Additional ventilation tests."""

    def test_unknown_space_type(self):
        room = _make_room(50, 5)
        with pytest.raises(ValueError, match='Unknown space type'):
            VentilationCheck(
                room, Q_(0.3, 'm**3/s'), space_type='spaceship',
            )

    def test_deficit_is_zero_when_compliant(self):
        room = _make_room(50, 5)
        vc = VentilationCheck(
            room, Q_(1.0, 'm**3/s'), 'office', oa_fraction=0.5,
        )
        assert vc.compliant is True
        assert vc.deficit.magnitude == 0

    def test_summary_compliant_format(self):
        room = _make_room(50, 8)
        vc = VentilationCheck(
            room, Q_(0.475, 'm**3/s'), 'office', oa_fraction=0.15,
        )
        s = vc.summary()
        assert 'COMPLIANT' in s
        assert 'provided' in s
        assert 'required' in s

    def test_summary_non_compliant_format(self):
        room = _make_room(60, 30)
        vc = VentilationCheck(
            room, Q_(0.2, 'm**3/s'), 'classroom', oa_fraction=0.15,
        )
        s = vc.summary()
        assert 'NON-COMPLIANT' in s
        assert 'deficit' in s

    def test_all_space_types_defined(self):
        """All required space types should be in the rates table."""
        expected = [
            'office', 'conference', 'classroom', 'retail', 'restaurant',
            'gym', 'hotel_room', 'hospital_ward', 'data_centre', 'corridor',
        ]
        for space in expected:
            assert space in VENTILATION_RATES

    def test_restaurant_ventilation(self):
        room = _make_room(80, 40)
        vc = VentilationCheck(
            room, Q_(0.5, 'm**3/s'), 'restaurant', oa_fraction=0.30,
        )
        # Rp=3.8, Ra=0.9: Vz = 3.8*40 + 0.9*80 = 224 L/s
        assert abs(vc.required_oa_flow.magnitude - 224.0) < 0.5

    def test_corridor_no_people_rate(self):
        room = _make_room(100, 0)
        vc = VentilationCheck(
            room, Q_(0.3, 'm**3/s'), 'corridor', oa_fraction=0.2,
        )
        # Rp=0, Ra=0.3: Vz = 0 + 0.3*100 = 30 L/s
        assert abs(vc.required_oa_flow.magnitude - 30.0) < 0.5
