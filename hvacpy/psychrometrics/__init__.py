"""Psychrometrics module — AirState class and convenience functions.

Provides the AirState class for representing moist air thermodynamic
states, and module-level convenience functions for quick calculations.

Example:
    >>> from hvacpy import Q_, AirState
    >>> office = AirState(dry_bulb=Q_(25, 'degC'), rh=0.60)
    >>> print(office.wet_bulb)
    19.38 degree_Celsius
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pint import Quantity

from hvacpy.exceptions import PsychrometricInputError
from hvacpy.units import Q_
from hvacpy.psychrometrics import _equations as _eq
from hvacpy.psychrometrics._equations import P_STD_PA, CP_DA, CP_WV, H_FG_0

if TYPE_CHECKING:
    pass

# Re-export AirProcess and PsychChart at package level.
from hvacpy.psychrometrics._process import AirProcess  # noqa: E402
from hvacpy.psychrometrics._chart import PsychChart  # noqa: E402

# Valid two-property input combinations (excluding pressure).
_VALID_COMBOS = {
    frozenset({"dry_bulb", "rh"}),
    frozenset({"dry_bulb", "wet_bulb"}),
    frozenset({"dry_bulb", "dew_point"}),
    frozenset({"dry_bulb", "humidity_ratio"}),
    frozenset({"dry_bulb", "enthalpy"}),
}


class AirState:
    """Thermodynamic state of moist air at a given pressure.

    Provide exactly two independent properties from the list below.
    All other properties are derived automatically and cached lazily.

    Args:
        dry_bulb: Dry bulb temperature as a Quantity (degC or degF or K).
        wet_bulb: Wet bulb temperature as a Quantity (degC or degF or K).
        dew_point: Dew point temperature as a Quantity (degC or degF or K).
        rh: Relative humidity as a plain float 0.0–1.0 (NOT a Quantity).
        humidity_ratio: Humidity ratio as a Quantity (dimensionless kg/kg).
        enthalpy: Specific enthalpy as a Quantity (J/kg or kJ/kg).
        pressure: Atmospheric pressure as a Quantity (Pa or kPa or bar).
            Defaults to 101325 Pa if not provided.

    Raises:
        PsychrometricInputError: If input combination is invalid,
            values are out of range, or types are wrong.
    """

    def __init__(
        self,
        *,
        dry_bulb: Quantity | None = None,
        wet_bulb: Quantity | None = None,
        dew_point: Quantity | None = None,
        rh: float | None = None,
        humidity_ratio: Quantity | None = None,
        enthalpy: Quantity | None = None,
        pressure: Quantity | None = None,
    ) -> None:
        # ── Parse pressure ──────────────────────────────────────
        if pressure is not None:
            self._p_pa: float = pressure.to("Pa").magnitude
        else:
            self._p_pa = P_STD_PA

        # ── Validate rh type ────────────────────────────────────
        if rh is not None and isinstance(rh, Quantity):
            raise PsychrometricInputError(
                "rh must be a plain float between 0.0 and 1.0, "
                "not a Quantity. For 60% RH use rh=0.60."
            )

        # ── Identify provided properties ────────────────────────
        prop_names: list[str] = []
        if dry_bulb is not None:
            prop_names.append("dry_bulb")
        if wet_bulb is not None:
            prop_names.append("wet_bulb")
        if dew_point is not None:
            prop_names.append("dew_point")
        if rh is not None:
            prop_names.append("rh")
        if humidity_ratio is not None:
            prop_names.append("humidity_ratio")
        if enthalpy is not None:
            prop_names.append("enthalpy")

        # ── Count check ─────────────────────────────────────────
        if len(prop_names) < 2:
            given = ", ".join(prop_names) if prop_names else "none"
            raise PsychrometricInputError(
                f"AirState requires exactly 2 independent properties. "
                f"Got: {given} only."
            )

        if len(prop_names) > 2:
            names_str = ", ".join(prop_names)
            raise PsychrometricInputError(
                f"AirState received {len(prop_names)} properties: "
                f"{names_str}. Provide exactly 2."
            )

        # ── Combination check ───────────────────────────────────
        combo = frozenset(prop_names)
        if combo not in _VALID_COMBOS:
            raise PsychrometricInputError(
                f"Invalid property combination: "
                f"{', '.join(sorted(prop_names))}. "
                f"All combinations require dry_bulb as one of "
                f"the two properties."
            )

        # ── Parse dry_bulb (always present for valid combos) ────
        self._t_db: float = float(dry_bulb.to("degC").magnitude)  # type: ignore[union-attr]

        # Validate dry_bulb range.
        if self._t_db < -100.0:
            raise PsychrometricInputError(
                f"dry_bulb ({self._t_db:.1f}°C) is below the valid "
                f"range of -100°C to 200°C."
            )
        if self._t_db > 200.0:
            raise PsychrometricInputError(
                f"dry_bulb ({self._t_db:.1f}°C) is above the valid "
                f"range of -100°C to 200°C."
            )

        # ── Validate rh range ───────────────────────────────────
        if rh is not None:
            if rh > 1.0:
                raise PsychrometricInputError(
                    f"rh must be between 0.0 and 1.0. Got {rh}. "
                    f"For {rh:.0f}% relative humidity use "
                    f"rh={rh / 100:.2f}."
                )
            if rh < 0.0:
                raise PsychrometricInputError(
                    f"rh must be between 0.0 and 1.0. Got {rh}."
                )

        # ── Validate wet_bulb ≤ dry_bulb ────────────────────────
        if wet_bulb is not None:
            t_wb_c = wet_bulb.to("degC").magnitude
            if t_wb_c > self._t_db:
                raise PsychrometricInputError(
                    f"wet_bulb ({t_wb_c:.1f}°C) cannot exceed "
                    f"dry_bulb ({self._t_db:.1f}°C)."
                )

        # ── Validate dew_point ≤ dry_bulb ───────────────────────
        if dew_point is not None:
            t_dp_c = dew_point.to("degC").magnitude
            if t_dp_c > self._t_db:
                raise PsychrometricInputError(
                    f"dew_point ({t_dp_c:.1f}°C) cannot exceed "
                    f"dry_bulb ({self._t_db:.1f}°C)."
                )

        # ── Determine humidity ratio W ──────────────────────────
        second_prop = next(iter(combo - {"dry_bulb"}))

        if second_prop == "rh":
            self._W: float = _eq.humidity_ratio_from_rh(
                self._t_db, rh, self._p_pa  # type: ignore[arg-type]
            )
        elif second_prop == "wet_bulb":
            t_wb_c = wet_bulb.to("degC").magnitude  # type: ignore[union-attr]
            self._W = _eq.humidity_ratio_from_wet_bulb(
                self._t_db, t_wb_c, self._p_pa
            )
        elif second_prop == "dew_point":
            t_dp_c = dew_point.to("degC").magnitude  # type: ignore[union-attr]
            self._W = _eq.humidity_ratio_from_dew_point(
                t_dp_c, self._p_pa
            )
        elif second_prop == "humidity_ratio":
            w_val = humidity_ratio.to("kg/kg").magnitude  # type: ignore[union-attr]
            if w_val < 0:
                raise PsychrometricInputError(
                    f"humidity_ratio cannot be negative. "
                    f"Got {w_val} kg/kg."
                )
            self._W = w_val
        elif second_prop == "enthalpy":
            h_j_kg = enthalpy.to("J/kg").magnitude  # type: ignore[union-attr]
            self._W = _eq.humidity_ratio_from_enthalpy_and_dbt(
                h_j_kg, self._t_db
            )
        else:
            raise PsychrometricInputError(
                f"Unexpected property: {second_prop}"
            )

        # ── Initialize cached property slots ────────────────────
        self._rh_cached: float | None = (
            rh if rh is not None else None
        )
        self._wet_bulb_cached: Quantity | None = (
            Q_(wet_bulb.to("degC").magnitude, "degC")  # type: ignore[union-attr]
            if wet_bulb is not None
            else None
        )
        self._dew_point_cached: Quantity | None = (
            Q_(dew_point.to("degC").magnitude, "degC")  # type: ignore[union-attr]
            if dew_point is not None
            else None
        )
        self._enthalpy_cached: Quantity | None = (
            Q_(enthalpy.to("J/kg").magnitude, "J/kg")  # type: ignore[union-attr]
            if enthalpy is not None
            else None
        )
        self._specific_volume_cached: Quantity | None = None
        self._density_cached: Quantity | None = None
        self._sat_vap_pressure_cached: Quantity | None = None
        self._vapour_pressure_cached: Quantity | None = None

    # ── Properties ──────────────────────────────────────────────

    @property
    def dry_bulb(self) -> Quantity:
        """Dry bulb temperature.

        Returns:
            Quantity: Temperature in °C.
        """
        return Q_(self._t_db, "degC")

    @property
    def wet_bulb(self) -> Quantity:
        """Wet bulb (adiabatic saturation) temperature.

        The temperature measured by a thermometer with its bulb
        covered in a wet wick exposed to moving air.

        Returns:
            Quantity: Wet bulb temperature in °C.
        """
        if self._wet_bulb_cached is None:
            self._wet_bulb_cached = Q_(
                _eq.wet_bulb_from_humidity_ratio(
                    self._t_db, self._W, self._p_pa
                ),
                "degC",
            )
        return self._wet_bulb_cached

    @property
    def dew_point(self) -> Quantity:
        """Dew point temperature.

        The temperature at which moist air becomes saturated when
        cooled at constant pressure and humidity ratio.

        Returns:
            Quantity: Dew point temperature in °C.
        """
        if self._dew_point_cached is None:
            self._dew_point_cached = Q_(
                _eq.dew_point_from_humidity_ratio(
                    self._t_db, self._W, self._p_pa
                ),
                "degC",
            )
        return self._dew_point_cached

    @property
    def rh(self) -> float:
        """Relative humidity as a decimal (0.0–1.0).

        The ratio of the actual water vapour partial pressure to
        the saturation pressure at the same dry bulb temperature.

        Returns:
            float: Relative humidity, NOT a Quantity.
        """
        if self._rh_cached is None:
            self._rh_cached = _eq.rh_from_humidity_ratio(
                self._t_db, self._W, self._p_pa
            )
        return self._rh_cached

    @property
    def humidity_ratio(self) -> Quantity:
        """Humidity ratio (mixing ratio) W.

        Mass of water vapour per unit mass of dry air.

        Returns:
            Quantity: Humidity ratio in kg/kg.
        """
        return Q_(self._W, "kg/kg")

    @property
    def enthalpy(self) -> Quantity:
        """Specific enthalpy of moist air.

        The total energy content per kilogram of dry air, including
        sensible heat of dry air and water vapour plus latent heat
        of vaporisation.

        Returns:
            Quantity: Enthalpy in J/kg dry air. (HOF 2021 Eq. 1-32)
                h = 1006*t_db + W*(2501000 + 1805*t_db)
        """
        if self._enthalpy_cached is None:
            self._enthalpy_cached = Q_(
                _eq.enthalpy_from_humidity_ratio(self._t_db, self._W),
                "J/kg",
            )
        return self._enthalpy_cached

    @property
    def specific_volume(self) -> Quantity:
        """Specific volume of moist air.

        Volume per unit mass of dry air.

        Returns:
            Quantity: Specific volume in m³/kg dry air.
        """
        if self._specific_volume_cached is None:
            self._specific_volume_cached = Q_(
                _eq.specific_volume(self._t_db, self._W, self._p_pa),
                "m³/kg",
            )
        return self._specific_volume_cached

    @property
    def density(self) -> Quantity:
        """Density of moist air.

        Returns:
            Quantity: Density in kg/m³.
        """
        if self._density_cached is None:
            self._density_cached = Q_(
                _eq.density(self._t_db, self._W, self._p_pa),
                "kg/m³",
            )
        return self._density_cached

    @property
    def pressure(self) -> Quantity:
        """Atmospheric pressure.

        Returns:
            Quantity: Pressure in Pa.
        """
        return Q_(self._p_pa, "Pa")

    @property
    def sat_vap_pressure(self) -> Quantity:
        """Saturation vapour pressure at dry bulb temperature.

        Returns:
            Quantity: Saturation vapour pressure in Pa.
        """
        if self._sat_vap_pressure_cached is None:
            self._sat_vap_pressure_cached = Q_(
                _eq.sat_vap_pressure(self._t_db),
                "Pa",
            )
        return self._sat_vap_pressure_cached

    @property
    def vapour_pressure(self) -> Quantity:
        """Partial pressure of water vapour.

        Returns:
            Quantity: Vapour pressure in Pa. = rh * sat_vap_pressure.
        """
        if self._vapour_pressure_cached is None:
            self._vapour_pressure_cached = Q_(
                self.rh * self.sat_vap_pressure.magnitude,
                "Pa",
            )
        return self._vapour_pressure_cached

    # ── Methods ─────────────────────────────────────────────────

    def __repr__(self) -> str:
        """Return string representation.

        Always shows dry_bulb, rh, W, and enthalpy in kJ/kg.
        """
        h_kj = self.enthalpy.to("kJ/kg").magnitude
        return (
            f"AirState(dry_bulb={self._t_db:.1f}°C, "
            f"rh={self.rh:.2f}, "
            f"W={self._W:.5f} kg/kg, "
            f"h={h_kj:.1f} kJ/kg)"
        )

    def to_dict(self) -> dict:
        """Return all properties as a dict of plain floats in SI.

        Returns:
            dict with keys: t_db_c, rh, W, t_wb_c, t_dp_c,
            h_j_kg, v_m3_kg, density_kg_m3, p_pa. All float.
        """
        return {
            "t_db_c": self._t_db,
            "rh": self.rh,
            "W": self._W,
            "t_wb_c": self.wet_bulb.magnitude,
            "t_dp_c": self.dew_point.magnitude,
            "h_j_kg": self.enthalpy.magnitude,
            "v_m3_kg": self.specific_volume.magnitude,
            "density_kg_m3": self.density.magnitude,
            "p_pa": self._p_pa,
        }

    def at_pressure(self, pressure: Quantity) -> "AirState":
        """Return a new AirState at a different pressure.

        Same dry_bulb and humidity_ratio, but different pressure.
        Useful for altitude corrections.

        Args:
            pressure: New atmospheric pressure as a Quantity.

        Returns:
            A new AirState instance. Does not modify self.
        """
        return AirState(
            dry_bulb=Q_(self._t_db, "degC"),
            humidity_ratio=Q_(self._W, "kg/kg"),
            pressure=pressure,
        )

    def mix_with(
        self,
        other: "AirState",
        self_mass_flow: Quantity,
        other_mass_flow: Quantity,
    ) -> "AirState":
        """Adiabatic mixing with another AirState.

        Args:
            other: The other AirState to mix with.
            self_mass_flow: Dry air mass flow rate for self,
                as a Quantity with mass/time dimensions (kg/s, etc.).
            other_mass_flow: Dry air mass flow rate for other.

        Returns:
            A new AirState at the mixed condition.

        Raises:
            PsychrometricInputError: If pressures differ by more
                than 1 Pa.
        """
        # Check pressures match.
        if abs(self._p_pa - other._p_pa) > 1.0:
            raise PsychrometricInputError(
                f"Cannot mix air streams at different pressures: "
                f"{self._p_pa:.0f} Pa vs {other._p_pa:.0f} Pa. "
                f"Pressures must match within 1 Pa."
            )

        m1 = self_mass_flow.to("kg/s").magnitude
        m2 = other_mass_flow.to("kg/s").magnitude

        t_db_mix, W_mix, _ = _eq.mix_airstreams(
            self._t_db, self._W, m1,
            other._t_db, other._W, m2,
            self._p_pa,
        )

        return AirState(
            dry_bulb=Q_(t_db_mix, "degC"),
            humidity_ratio=Q_(W_mix, "kg/kg"),
            pressure=Q_(self._p_pa, "Pa"),
        )


# ── Module-level Convenience Functions ──────────────────────────────


def humidity_ratio_from_rh(
    t_db: Quantity,
    rh: float,
    pressure: Quantity | None = None,
) -> Quantity:
    """Return humidity ratio W from dry bulb and relative humidity.

    Convenience function wrapping AirState.

    Args:
        t_db: Dry bulb temperature as a Quantity.
        rh: Relative humidity as plain float 0.0–1.0.
        pressure: Atmospheric pressure as a Quantity. Defaults
            to 101325 Pa.

    Returns:
        Humidity ratio as Quantity (kg/kg).
    """
    kwargs: dict = {"dry_bulb": t_db, "rh": rh}
    if pressure is not None:
        kwargs["pressure"] = pressure
    state = AirState(**kwargs)
    return state.humidity_ratio


def dew_point_from_humidity_ratio(
    W: Quantity,
    pressure: Quantity | None = None,
) -> Quantity:
    """Return dew point temperature from humidity ratio.

    Convenience function. Constructs an AirState internally using
    a nominal dry_bulb of 25°C (W is independent of dry_bulb for
    dew point calculation).

    Args:
        W: Humidity ratio as a Quantity (kg/kg).
        pressure: Atmospheric pressure as a Quantity.

    Returns:
        Dew point as Quantity (degC).
    """
    # Dew point depends only on W and pressure, not on dry_bulb.
    # Use a nominal dry_bulb that is >= the dew point to avoid
    # validation errors.
    w_val = W.to("kg/kg").magnitude
    p_pa = pressure.to("Pa").magnitude if pressure else P_STD_PA
    t_dp = _eq.dew_point_from_humidity_ratio(50.0, w_val, p_pa)
    # Use a dry_bulb safely above the dew point.
    t_db_safe = max(t_dp + 5.0, 25.0)
    kwargs: dict = {
        "dry_bulb": Q_(t_db_safe, "degC"),
        "humidity_ratio": W,
    }
    if pressure is not None:
        kwargs["pressure"] = pressure
    state = AirState(**kwargs)
    return state.dew_point


def dry_bulb_from_wet_bulb(
    t_wb: Quantity,
    rh: float,
    pressure: Quantity | None = None,
) -> Quantity:
    """Return dry bulb temperature given wet bulb and RH.

    Uses iterative solving — convergence tolerance 0.001°C.

    Args:
        t_wb: Wet bulb temperature as a Quantity.
        rh: Relative humidity as plain float 0.0–1.0.
        pressure: Atmospheric pressure as a Quantity.

    Returns:
        Dry bulb temperature as Quantity (degC).

    Raises:
        PsychrometricInputError: If convergence fails.
    """
    t_wb_c = t_wb.to("degC").magnitude
    p_pa = pressure.to("Pa").magnitude if pressure else P_STD_PA

    # Iterative solve: dry_bulb >= wet_bulb always.
    # Start with an initial guess.
    t_db_guess = t_wb_c + 5.0
    tolerance = 0.001
    max_iter = 200

    for _ in range(max_iter):
        W = _eq.humidity_ratio_from_rh(t_db_guess, rh, p_pa)
        t_wb_calc = _eq.wet_bulb_from_humidity_ratio(
            t_db_guess, W, p_pa
        )
        error = t_wb_calc - t_wb_c

        if abs(error) < tolerance:
            return Q_(t_db_guess, "degC")

        # Adjust: if calculated wb is too high, dry_bulb is too low
        # (or rh is too high for the guess). Use Newton-like step.
        # Derivative is approximately d(t_wb)/d(t_db) ≈ rh
        # (rough approximation for convergence).
        t_db_guess -= error / max(rh, 0.1)

    raise PsychrometricInputError(
        f"dry_bulb_from_wet_bulb failed to converge after "
        f"{max_iter} iterations for t_wb={t_wb_c}°C, rh={rh}."
    )


def sat_pressure(t_db: Quantity) -> Quantity:
    """Return saturation vapour pressure at the given temperature.

    Args:
        t_db: Temperature as a Quantity.

    Returns:
        Saturation vapour pressure as Quantity (Pa).
    """
    t_c = t_db.to("degC").magnitude
    return Q_(_eq.sat_vap_pressure(t_c), "Pa")


# Public API exports.
__all__ = [
    "AirState",
    "AirProcess",
    "PsychChart",
    "humidity_ratio_from_rh",
    "dew_point_from_humidity_ratio",
    "dry_bulb_from_wet_bulb",
    "sat_pressure",
]
