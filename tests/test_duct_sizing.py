"""Tests for duct sizing — v0.4.

Test group D from the spec.
"""

from __future__ import annotations

import math

import pytest

from hvacpy.units import Q_
from hvacpy.exceptions import DuctSizingError
from hvacpy.equipment._duct import DuctSizer


# ═══════════════════════════════════════════════════════════════════
# GROUP D — Duct Sizing
# ═══════════════════════════════════════════════════════════════════


class TestEqualFriction:
    """E-D01, E-D02: Equal friction method."""

    def test_e_d01_equal_friction_0_2(self):
        """0.2 m³/s at 0.8 Pa/m → brentq solves D ≈ 258mm → rounds up to 300mm."""
        ds = DuctSizer(Q_(0.2, 'm**3/s'), method='equal_friction')
        assert ds.diameter.magnitude == 300
        # V = 0.2 / (π/4 × 0.300²) ≈ 2.83 m/s
        assert abs(ds.velocity.magnitude - 2.83) < 0.2
        assert ds.friction_loss.magnitude > 0

    def test_e_d02_equal_friction_0_5_rounding(self):
        """0.5 m³/s at 0.8 Pa/m → D exact ≈ 364mm → rounds up to 400mm standard size."""
        ds = DuctSizer(Q_(0.5, 'm**3/s'), method='equal_friction')
        assert ds.diameter.magnitude == 400
        # Actual friction is ≤ 0.8 Pa/m since duct is rounded up
        assert ds.friction_loss.magnitude <= 0.8

    def test_equal_friction_custom_rate(self):
        ds = DuctSizer(Q_(0.3, 'm**3/s'), friction_rate=1.0)
        assert ds.diameter.magnitude > 0

    def test_exact_vs_standard(self):
        """diameter_exact should be <= diameter (standard)."""
        ds = DuctSizer(Q_(0.3, 'm**3/s'))
        assert ds.diameter_exact.magnitude <= ds.diameter.magnitude


class TestVelocityReduction:
    """E-D03, E-D05: Velocity reduction method."""

    def test_e_d03_branch_duct(self):
        ds = DuctSizer(
            Q_(0.1, 'm**3/s'),
            method='velocity_reduction',
            section_type='branch_supply',
        )
        # V_max=5.0, D=sqrt(4*0.1/(pi*5))=0.160m → 175mm
        assert ds.diameter.magnitude == 175
        assert ds.velocity.magnitude < 5.0
        assert ds.velocity_ok is True

    def test_e_d05_main_duct(self):
        ds = DuctSizer(
            Q_(1.0, 'm**3/s'),
            method='velocity_reduction',
            section_type='main_supply',
        )
        # V_max=7.5
        assert ds.velocity.magnitude <= 7.5
        assert ds.velocity_ok is True

    def test_velocity_reduction_return_duct(self):
        ds = DuctSizer(
            Q_(0.2, 'm**3/s'),
            method='velocity_reduction',
            section_type='return',
        )
        assert ds.velocity.magnitude <= 5.0
        assert ds.velocity_ok is True


class TestRectangularEquivalent:
    """E-D04: Rectangular equivalent duct sizing."""

    def test_e_d04_aspect_ratio(self):
        ds = DuctSizer(Q_(0.3, 'm**3/s'), method='equal_friction')
        w, h = ds.rectangular_equivalent
        # Width and height should be in reasonable range
        assert 100 <= w <= 1000
        assert 100 <= h <= 1000
        # Aspect ratio should be approximately 1.5:1
        ratio = w / h
        assert 1.3 <= ratio <= 1.7
        # Both should be multiples of 50mm
        assert w % 50 == 0
        assert h % 50 == 0

    def test_rectangular_in_summary(self):
        ds = DuctSizer(Q_(0.3, 'm**3/s'))
        s = ds.summary()
        assert 'Dia' in s
        assert 'rect' in s


class TestStaticRegain:
    """Static regain method edge cases."""

    def test_static_regain_basic(self):
        """Reducing section: 0.2 m³/s, V1=7 m/s, L=10 m → brentq finds D where regain equals friction."""
        ds = DuctSizer(
            Q_(0.2, 'm**3/s'),
            method='static_regain',
            upstream_velocity=7.0,
            section_length=10.0,
        )
        assert ds.diameter.magnitude > 0
        assert ds.velocity.magnitude > 0

    def test_static_regain_requires_params(self):
        with pytest.raises(DuctSizingError, match='upstream_velocity'):
            DuctSizer(Q_(0.3, 'm**3/s'), method='static_regain')


class TestDuctSizerMisc:
    """Miscellaneous DuctSizer tests."""

    def test_unknown_method(self):
        with pytest.raises(ValueError, match='Unknown duct sizing method'):
            DuctSizer(Q_(0.3, 'm**3/s'), method='foo')

    def test_summary_format(self):
        ds = DuctSizer(Q_(0.2, 'm**3/s'))
        s = ds.summary()
        assert 'Dia' in s
        assert 'm/s' in s
        assert 'Pa/m' in s
        assert 'rect' in s

    def test_friction_loss_property(self):
        ds = DuctSizer(Q_(0.2, 'm**3/s'))
        assert ds.friction_loss.magnitude > 0

    def test_velocity_property(self):
        ds = DuctSizer(Q_(0.2, 'm**3/s'))
        assert ds.velocity.magnitude > 0
