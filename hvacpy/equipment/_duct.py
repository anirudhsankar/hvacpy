"""Duct sizing — ASHRAE HOF 2021 Ch.21.

Three methods: equal friction, velocity reduction, static regain.
Uses scipy.optimize.brentq for Colebrook-White and sizing iterations.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from scipy.optimize import brentq

from hvacpy.units import Q_
from hvacpy.exceptions import DuctSizingError

if TYPE_CHECKING:
    from pint import Quantity

# ── Physical Constants ──────────────────────────────────────────────

EPS = 0.00009          # m — surface roughness (galvanized steel)
NU = 1.5e-5            # m²/s — kinematic viscosity of air
RHO_AIR = 1.2          # kg/m³
DEFAULT_FRICTION = 0.8 # Pa/m

# Velocity limits by section type
V_MAX: dict[str, float] = {
    'main_supply':   7.5,
    'branch_supply': 5.0,
    'return':        5.0,
}

# Standard circular duct sizes (mm)
STANDARD_SIZES_MM = [
    100, 125, 150, 175, 200, 225, 250, 300, 350, 400,
    450, 500, 560, 630, 710, 800, 900, 1000, 1120, 1250,
]


def _next_std_size_mm(d_mm: float) -> int:
    """Return smallest standard duct size >= d_mm."""
    for s in STANDARD_SIZES_MM:
        if s >= d_mm:
            return s
    return STANDARD_SIZES_MM[-1]


def _friction_factor(d: float, v: float) -> float:
    """Solve Colebrook-White for Darcy friction factor.

    1/sqrt(f) = -2.0*log10(eps/(3.7*D) + 2.51/(Re*sqrt(f)))
    """
    re = v * d / NU
    if re < 100:
        re = 100  # avoid singularity

    def residual(f):
        return (1.0 / math.sqrt(f)
                + 2.0 * math.log10(EPS / (3.7 * d) + 2.51 / (re * math.sqrt(f))))

    try:
        f = brentq(residual, 0.005, 0.1)
    except ValueError:
        # Fallback if brentq fails (e.g. roots have same sign due to extreme velocity)
        f = 0.02
    return f


def _friction_loss(d: float, v: float) -> float:
    """Friction loss dP/L in Pa/m using Darcy-Weisbach.

    dP/L = f * rho * V^2 / (2*D)
    """
    f = _friction_factor(d, v)
    return f * RHO_AIR * v**2 / (2.0 * d)


def _velocity_in_duct(v_dot: float, d: float) -> float:
    """Velocity (m/s) for flow V_dot (m³/s) in circular duct diameter d (m)."""
    area = math.pi * d**2 / 4.0
    return v_dot / area


# ── Equal Friction Method ───────────────────────────────────────────

def _equal_friction_diameter(v_dot: float, friction_rate: float) -> float:
    """Find diameter D so dP/L = friction_rate.

    Uses brentq with D bracket [0.05, 2.0] m.
    """
    def residual(d):
        v = _velocity_in_duct(v_dot, d)
        return _friction_loss(d, v) - friction_rate

    d = brentq(residual, 0.05, 2.0)
    return d


# ── Velocity Reduction Method ──────────────────────────────────────

def _velocity_reduction_diameter(v_dot: float, v_max: float) -> float:
    """Find diameter D for maximum velocity V_max.

    D = sqrt(4*V_dot/(pi*V_max))
    """
    return math.sqrt(4.0 * v_dot / (math.pi * v_max))


# ── Static Regain Method ───────────────────────────────────────────

def _static_regain_diameter(
    v_dot: float, upstream_velocity: float,
    section_length: float, max_iter: int = 50,
) -> float:
    """Size section so static regain equals friction loss.

    R*(V1²-V2²)*rho/2 = f2*(rho*V2²/2)*(L2/D2)
    R = 0.75. Solve using brentq.
    """
    R = 0.75

    def regain_residual(d):
        v2 = _velocity_in_duct(v_dot, d)
        f2 = _friction_factor(d, v2)
        regain = R * (upstream_velocity**2 - v2**2) * RHO_AIR / 2.0
        friction = f2 * (RHO_AIR * v2**2 / 2.0) * (section_length / d)
        return regain - friction

    try:
        # Search between 10mm and 2000mm
        d = brentq(regain_residual, 0.01, 2.0)
        return d
    except ValueError:
        # If no root in range (e.g. friction always > regain), try velocity reduction fallback
        v_target = upstream_velocity * 0.9
        if v_target <= 0:
            v_target = 1.0
        return _velocity_reduction_diameter(v_dot, v_target)


# ── Rectangular Equivalent ──────────────────────────────────────────

def _rectangular_equivalent(d_m: float) -> tuple[int, int]:
    """Find rectangular duct (a x b) equivalent to circular D.

    D_eq = 1.30 * (a*b)^0.625 / (a+b)^0.250
    Aspect ratio 1.5:1 → a = 1.5*b. Solve for b with brentq.
    Round a and b UP to nearest 50mm.
    """
    def residual(b):
        a = 1.5 * b
        d_eq = 1.30 * (a * b)**0.625 / (a + b)**0.250
        return d_eq - d_m

    b = brentq(residual, 0.02, 2.0)
    a = 1.5 * b

    # Round UP to nearest 50mm
    a_mm = int(math.ceil(a * 1000 / 50.0)) * 50
    b_mm = int(math.ceil(b * 1000 / 50.0)) * 50

    return (a_mm, b_mm)


# ── DuctSizer Class ─────────────────────────────────────────────────

class DuctSizer:
    """Duct sizing using equal friction, velocity reduction, or static regain.

    Args:
        airflow: Volume flow rate as Quantity (m³/s).
        method: 'equal_friction', 'velocity_reduction', or 'static_regain'.
        section_type: 'main_supply', 'branch_supply', or 'return'.
        friction_rate: Target friction rate in Pa/m (equal friction only).
        upstream_velocity: Upstream velocity in m/s (static regain only).
        section_length: Section length in m (static regain only).
    """

    def __init__(
        self,
        airflow: 'Quantity',
        method: str = 'equal_friction',
        section_type: str = 'main_supply',
        friction_rate: float | None = None,
        upstream_velocity: float | None = None,
        section_length: float | None = None,
    ) -> None:
        self._v_dot = airflow.to('m**3/s').magnitude
        self._method = method
        self._section_type = section_type
        self._v_max = V_MAX.get(section_type, 7.5)

        if friction_rate is None:
            friction_rate = DEFAULT_FRICTION

        # Calculate exact diameter
        if method == 'equal_friction':
            d_exact = _equal_friction_diameter(self._v_dot, friction_rate)
        elif method == 'velocity_reduction':
            d_exact = _velocity_reduction_diameter(self._v_dot, self._v_max)
        elif method == 'static_regain':
            if upstream_velocity is None or section_length is None:
                raise DuctSizingError(
                    "Static regain method requires upstream_velocity "
                    "and section_length."
                )
            d_exact = _static_regain_diameter(
                self._v_dot, upstream_velocity, section_length,
            )
        else:
            raise ValueError(f"Unknown duct sizing method: '{method}'")

        self._d_exact_mm = d_exact * 1000.0
        self._d_std_mm = _next_std_size_mm(self._d_exact_mm)
        d_std_m = self._d_std_mm / 1000.0

        # Actual velocity and friction in sized duct
        self._velocity = _velocity_in_duct(self._v_dot, d_std_m)
        self._friction_loss = _friction_loss(d_std_m, self._velocity)

        # Rectangular equivalent
        self._rect = _rectangular_equivalent(d_std_m)

    @property
    def diameter(self) -> 'Quantity':
        """Rounded up to nearest standard size (mm)."""
        return Q_(self._d_std_mm, 'mm')

    @property
    def diameter_exact(self) -> 'Quantity':
        """Before rounding (mm)."""
        return Q_(self._d_exact_mm, 'mm')

    @property
    def velocity(self) -> 'Quantity':
        """Actual velocity in sized duct (m/s)."""
        return Q_(self._velocity, 'm/s')

    @property
    def friction_loss(self) -> 'Quantity':
        """Actual friction at sized diameter (Pa/m)."""
        return Q_(self._friction_loss, 'Pa/m')

    @property
    def velocity_ok(self) -> bool:
        """True if velocity <= V_max for section_type."""
        return self._velocity <= self._v_max

    @property
    def rectangular_equivalent(self) -> tuple:
        """(width_mm, height_mm) at 1.5:1 aspect, rounded to nearest 50mm."""
        return self._rect

    def summary(self) -> str:
        """One-line summary: 'Dia250mm - 4.1m/s - 0.72Pa/m - or 300x200mm rect'."""
        w, h = self._rect
        return (
            f"Dia{self._d_std_mm:.0f}mm - "
            f"{self._velocity:.1f}m/s - "
            f"{self._friction_loss:.2f}Pa/m - "
            f"or {w}x{h}mm rect"
        )
