"""Internal gain and infiltration test cases.

Tests L-A08, L-A09, L-A10, L-A11 from the specification.
"""

import pytest

from hvacpy.loads._internal import (
    calculate_people_gain,
    calculate_lighting_gain,
    calculate_equipment_gain,
    BALLAST_FACTOR,
)
from hvacpy.loads._infiltration import (
    calculate_infiltration_mass_flow,
    calculate_infiltration_sensible,
    calculate_infiltration_latent,
    CP_DA,
    DENSITY_AIR,
)


# ── People Gains ────────────────────────────────────────────────────

class TestPeopleGains:
    """TEST L-A08 — People sensible + latent, office activity."""

    def test_la08_office_work(self) -> None:
        s, l = calculate_people_gain(
            count=10, activity='office_work', diversity=1.0, clf=1.0,
        )
        assert s == 650.0    # 10 * 65 * 1.0 * 1.0
        assert l == 550.0    # 10 * 55 * 1.0 (no CLF for latent)

    def test_people_with_diversity(self) -> None:
        s, l = calculate_people_gain(
            count=10, activity='office_work', diversity=0.8, clf=0.9,
        )
        assert abs(s - 10 * 65 * 0.8 * 0.9) < 0.01
        assert abs(l - 10 * 55 * 0.8) < 0.01  # no CLF

    def test_people_heavy_work(self) -> None:
        s, l = calculate_people_gain(
            count=5, activity='heavy_work', diversity=1.0, clf=1.0,
        )
        assert s == 5 * 185
        assert l == 5 * 250

    def test_people_latent_no_clf(self) -> None:
        """Verify latent is NOT multiplied by CLF."""
        _, l_with_clf = calculate_people_gain(
            count=10, activity='office_work', diversity=1.0, clf=0.5,
        )
        _, l_without_clf = calculate_people_gain(
            count=10, activity='office_work', diversity=1.0, clf=1.0,
        )
        assert l_with_clf == l_without_clf  # latent unaffected by CLF


# ── Lighting Gains ──────────────────────────────────────────────────

class TestLightingGains:
    """TEST L-A09 — Lighting gain."""

    def test_la09_lighting_watts_per_m2(self) -> None:
        q = calculate_lighting_gain(
            watts_per_m2=12.0, floor_area_m2=50.0,
            diversity=0.9, clf=1.0,
        )
        # total_watts = 12 * 50 = 600
        # Q = 600 * 0.9 * 1.0 * 1.25 (ballast) = 675 W
        assert q == 675.0

    def test_lighting_total_watts_priority(self) -> None:
        """total_watts takes priority over watts_per_m2."""
        q = calculate_lighting_gain(
            total_watts=1000, watts_per_m2=12.0, floor_area_m2=50.0,
            diversity=1.0, clf=1.0,
        )
        assert abs(q - 1000 * 1.0 * 1.0 * BALLAST_FACTOR) < 0.01

    def test_lighting_all_sensible(self) -> None:
        """Lighting gain is all sensible — function returns single float."""
        q = calculate_lighting_gain(total_watts=100, diversity=1.0, clf=1.0)
        assert isinstance(q, float)


# ── Equipment Gains ─────────────────────────────────────────────────

class TestEquipmentGains:
    """TEST L-A10 — Equipment gain."""

    def test_la10_equipment(self) -> None:
        s, l = calculate_equipment_gain(
            total_watts=800, diversity=0.8, clf=1.0,
        )
        # Q_total = 800 * 0.8 * 1.0 = 640 W
        # Q_sensible = 640 * 0.7 = 448 W
        # Q_latent = 640 * 0.3 = 192 W
        assert abs(s - 448.0) < 0.01
        assert abs(l - 192.0) < 0.01

    def test_equipment_watts_per_m2(self) -> None:
        s, l = calculate_equipment_gain(
            watts_per_m2=15.0, floor_area_m2=50.0,
            diversity=1.0, clf=1.0,
        )
        total = 15.0 * 50.0
        assert abs(s - total * 0.7) < 0.01
        assert abs(l - total * 0.3) < 0.01


# ── Infiltration ────────────────────────────────────────────────────

class TestInfiltration:
    """TEST L-A11 — Infiltration sensible only."""

    def test_la11_infiltration_sensible(self) -> None:
        # volume = 50m² * 3m = 150 m³, ACH = 0.5
        m_dot = calculate_infiltration_mass_flow(ach=0.5, volume_m3=150.0)
        # m_dot = 1.2 * 0.5 * 150 / 3600 = 0.025 kg/s
        assert abs(m_dot - 0.025) < 0.001

        q_sens = calculate_infiltration_sensible(
            m_dot=m_dot, t_outdoor_c=35.0, t_indoor_c=24.0,
        )
        # Q = 0.025 * 1006 * 11 = 276.65 W
        assert abs(q_sens - 276.65) < 5.0

    def test_infiltration_latent(self) -> None:
        m_dot = calculate_infiltration_mass_flow(ach=0.5, volume_m3=150.0)
        q_lat = calculate_infiltration_latent(m_dot=m_dot)
        # Default W_outdoor=0.010, W_indoor=0.0085
        # Q = 0.025 * 2501000 * (0.010 - 0.0085) = 0.025 * 2501000 * 0.0015
        # = 93.8 W
        assert q_lat > 0

    def test_mass_flow_formula(self) -> None:
        m_dot = calculate_infiltration_mass_flow(ach=1.0, volume_m3=100.0)
        expected = DENSITY_AIR * 1.0 * 100.0 / 3600.0
        assert abs(m_dot - expected) < 1e-6
