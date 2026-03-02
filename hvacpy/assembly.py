"""Assembly module — layered building envelope elements.

An Assembly represents a wall, roof, floor, or ceiling made of
stacked material layers. It calculates total thermal resistance
(R-value) and thermal transmittance (U-value) using the series
resistance method from ISO 6946:2017.

Example:
    >>> from hvacpy import Q_, db, Assembly
    >>> wall = Assembly('My Wall')
    >>> wall.add_layer('brick_common', Q_(110, 'mm'))
    >>> wall.add_layer('mineral_wool_batt', Q_(100, 'mm'))
    >>> wall.add_layer('plasterboard_std', Q_(12.5, 'mm'))
    >>> print(wall.u_value)
    0.298... W / K / m²
"""

from __future__ import annotations

from pint import Quantity

from hvacpy.exceptions import UnitError
from hvacpy.materials import Material, _DB
from hvacpy.units import Q_, validate_unit

# Surface resistance values — ISO 6946:2017 Table 1
# Named constants per spec Section 9.2, no magic numbers.
R_SI_WALL = 0.13  # m²K/W — horizontal heat flow
R_SI_ROOF = 0.10  # m²K/W — upward heat flow
R_SI_FLOOR = 0.17  # m²K/W — downward heat flow
R_SE = 0.04  # m²K/W — all orientations

_R_SI_MAP: dict[str, float] = {
    "wall": R_SI_WALL,
    "roof": R_SI_ROOF,
    "floor": R_SI_FLOOR,
}

_VALID_ORIENTATIONS = frozenset(_R_SI_MAP.keys())


class Assembly:
    """A layered building envelope element.

    Layers are ordered outside-to-inside. Surface resistances are
    added automatically based on orientation.

    Args:
        name: Human-readable description e.g. 'Brick Cavity Wall'.
        orientation: 'wall' | 'roof' | 'floor'. Defaults to 'wall'.

    Raises:
        ValueError: If orientation is not 'wall', 'roof', or 'floor'.
    """

    def __init__(self, name: str, orientation: str = "wall") -> None:
        if orientation not in _VALID_ORIENTATIONS:
            raise ValueError(
                f"orientation must be 'wall', 'roof', or 'floor', "
                f"got '{orientation}'"
            )
        self._name = name
        self._orientation = orientation
        self._r_si: float = _R_SI_MAP[orientation]
        self._r_se: float = R_SE
        # Internal layer storage — plain floats in SI units.
        self._layers: list[dict] = []

    def add_layer(
        self,
        material: str | Material,
        thickness: Quantity,
    ) -> "Assembly":
        """Add a material layer to this assembly.

        Layers are ordered as added, outside to inside.

        Args:
            material: Material key string (e.g. 'brick_common') or a
                Material instance. String keys are case-insensitive.
            thickness: Layer thickness as a pint Quantity with length
                units. E.g. Q_(110, 'mm') or Q_(0.11, 'm').

        Returns:
            self, enabling method chaining.

        Raises:
            TypeError: If thickness is not a pint Quantity.
            UnitError: If thickness does not have length dimensions.
            ValueError: If thickness is not positive.
            MaterialNotFoundError: If material is a string key not
                in DB.
        """
        # Validate thickness type.
        if not isinstance(thickness, Quantity):
            raise TypeError(
                f"thickness must be a pint Quantity, got "
                f"{type(thickness).__name__}. "
                f'Use Q_(value, unit) e.g. Q_(110, "mm")'
            )

        # Validate thickness dimensionality.
        validate_unit(thickness, "[length]", "thickness")

        # Convert to metres (SI).
        thickness_m: float = thickness.to("m").magnitude

        # Validate positive.
        if thickness_m <= 0:
            raise ValueError(
                f"thickness must be positive, got {thickness}"
            )

        # Resolve material.
        db_key: str | None = None
        if isinstance(material, str):
            db_key = material.lower()
            mat = _DB.get(material)
        elif isinstance(material, Material):
            mat = material
        else:
            raise TypeError(
                f"material must be a str or Material, got "
                f"{type(material).__name__}"
            )

        conductivity: float = mat.conductivity.to("W/(m*K)").magnitude
        r_layer: float = thickness_m / conductivity

        self._layers.append({
            "name": mat.name,
            "key": db_key,
            "thickness_m": thickness_m,
            "conductivity": conductivity,
            "r_layer": r_layer,
        })

        return self

    @property
    def r_value(self) -> Quantity:
        """Total thermal resistance including surface resistances.

        Returns:
            R-value as a pint Quantity in m²·K/W.
        """
        r_total = self._r_si + self._r_se
        for layer in self._layers:
            r_total += layer["r_layer"]
        return Q_(r_total, "m²*K/W")

    @property
    def u_value(self) -> Quantity:
        """Thermal transmittance (reciprocal of R-value).

        Returns:
            U-value as a pint Quantity in W/(m²·K).
        """
        r_total = self.r_value.magnitude
        return Q_(1.0 / r_total, "W/(m²*K)")

    @property
    def layers(self) -> list[dict]:
        """Layer information as list of dicts.

        Each dict contains:
            - name (str): Material name.
            - key (str | None): DB key if looked up, None if passed
              as Material instance.
            - thickness_m (float): Thickness in metres.
            - conductivity (float): W/(m·K).
            - r_layer (float): Layer resistance in m²K/W.
            - r_fraction (float): Layer R as fraction of total layer
              R (excludes surface resistances), 0.0–1.0.

        Returns:
            List of layer dicts ordered outside-to-inside.
        """
        r_layers_total = sum(
            layer["r_layer"] for layer in self._layers
        )

        result: list[dict] = []
        for layer in self._layers:
            fraction = (
                layer["r_layer"] / r_layers_total
                if r_layers_total > 0
                else 0.0
            )
            result.append({
                "name": layer["name"],
                "key": layer["key"],
                "thickness_m": layer["thickness_m"],
                "conductivity": layer["conductivity"],
                "r_layer": layer["r_layer"],
                "r_fraction": fraction,
            })

        return result

    def breakdown(self) -> str:
        """Human-readable breakdown of the assembly.

        Returns:
            Formatted string showing all layers, their resistances,
            surface resistances, and total R/U values.
        """
        r_total = self.r_value.magnitude
        u_val = self.u_value.magnitude

        lines: list[str] = []
        lines.append(
            f"Wall: {self._name}  "
            f"(orientation: {self._orientation})"
        )
        lines.append("━" * 47)
        lines.append("  [outside]")
        lines.append(
            f"  Surface resistance (R_se)"
            f"       {self._r_se:.3f} m²K/W"
        )
        lines.append("  " + "─" * 45)

        for layer in self._layers:
            thickness_mm = layer["thickness_m"] * 1000
            # Format thickness — show decimal only if needed.
            if thickness_mm == int(thickness_mm):
                t_str = f"{int(thickness_mm)} mm"
            else:
                t_str = f"{thickness_mm:.1f} mm"

            # Use key if available, otherwise name.
            label = layer["key"] if layer["key"] else layer["name"]
            lines.append(
                f"  {label:<16s}{t_str:>8s}"
                f"          {layer['r_layer']:.3f} m²K/W"
            )

        lines.append("  " + "─" * 45)
        lines.append(
            f"  Surface resistance (R_si)"
            f"       {self._r_si:.3f} m²K/W"
        )
        lines.append("  [inside]")
        lines.append("━" * 47)
        lines.append(f"  R_total   =  {r_total:.3f} m²K/W")
        lines.append(f"  U_value   =  {u_val:.3f} W/(m²K)")

        return "\n".join(lines)
