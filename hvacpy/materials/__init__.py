"""Materials module — Material dataclass and MaterialsDB registry.

Provides a database of building materials with thermal properties for
use in assembly thermal resistance calculations.

Example:
    >>> from hvacpy import db
    >>> brick = db.get('brick_common')
    >>> print(brick.conductivity)
    0.72 W / K / m
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any

from pint import Quantity

from hvacpy.exceptions import MaterialNotFoundError
from hvacpy.materials._database import MATERIALS
from hvacpy.units import Q_

# Allowed material categories — enforced on Material creation.
_ALLOWED_CATEGORIES = frozenset({
    "masonry",
    "insulation",
    "wood",
    "metal",
    "glazing",
    "membrane",
    "air",
    "finish",
    "concrete",
})


@dataclass(frozen=True)
class Material:
    """A building material with thermal properties.

    Attributes:
        name: Human-readable material name.
        conductivity: Thermal conductivity in W/(m·K).
        density: Material density in kg/m³.
        specific_heat: Specific heat capacity in J/(kg·K).
        category: Material category. Must be one of: masonry,
            insulation, wood, metal, glazing, membrane, air,
            finish, concrete.
        source: Reference source, e.g. 'ASHRAE HOF 2021 Table 1'.
    """

    name: str
    conductivity: Quantity  # W/(m·K)
    density: Quantity  # kg/m³
    specific_heat: Quantity  # J/(kg·K)
    category: str
    source: str

    def __post_init__(self) -> None:
        """Validate category on creation."""
        if self.category not in _ALLOWED_CATEGORIES:
            raise ValueError(
                f"category must be one of {sorted(_ALLOWED_CATEGORIES)}, "
                f"got '{self.category}'"
            )


class MaterialsDB:
    """Registry of building materials.

    The database contains built-in materials from ASHRAE and ISO
    standards, and supports adding custom materials at runtime.

    This class should not be instantiated directly by users. Use the
    module-level ``_DB`` singleton instead, exposed as ``db`` in the
    top-level ``hvacpy`` package.
    """

    def __init__(self) -> None:
        """Initialize the database with built-in materials."""
        self._builtin_keys: frozenset[str] = frozenset(MATERIALS.keys())
        self._builtin_materials: dict[str, Material] = {}
        self._custom_materials: dict[str, Material] = {}
        self._lock = threading.Lock()

        # Convert raw dicts to Material instances.
        for key, data in MATERIALS.items():
            self._builtin_materials[key] = _dict_to_material(data)

    def get(self, key: str) -> Material:
        """Return the Material for the given key.

        Args:
            key: Material identifier, case-insensitive.
                E.g. 'brick_common' or 'BRICK_COMMON'.

        Returns:
            The matching Material instance.

        Raises:
            MaterialNotFoundError: If no material matches the key.
                The error message includes the key and a hint to use
                list_keys().
        """
        normalized = key.lower()

        # Check built-ins first, then custom.
        material = self._builtin_materials.get(normalized)
        if material is not None:
            return material

        material = self._custom_materials.get(normalized)
        if material is not None:
            return material

        raise MaterialNotFoundError(
            f"Material '{key}' not found. "
            f"Use list_keys() to see available materials."
        )

    def list_keys(self) -> list[str]:
        """Return a sorted list of all available material keys.

        Returns:
            Sorted list of material key strings.
        """
        all_keys = set(self._builtin_materials.keys())
        all_keys.update(self._custom_materials.keys())
        return sorted(all_keys)

    def list_by_category(self, category: str) -> list[Material]:
        """Return materials filtered by category, sorted by name.

        Args:
            category: Category to filter by. Must be one of the
                allowed categories (masonry, insulation, wood, etc.).

        Returns:
            List of Material instances sorted by name.

        Raises:
            ValueError: If category is not in the allowed list.
        """
        if category not in _ALLOWED_CATEGORIES:
            raise ValueError(
                f"category must be one of {sorted(_ALLOWED_CATEGORIES)}, "
                f"got '{category}'"
            )

        results: list[Material] = []
        for mat in self._builtin_materials.values():
            if mat.category == category:
                results.append(mat)
        for mat in self._custom_materials.values():
            if mat.category == category:
                results.append(mat)

        return sorted(results, key=lambda m: m.name)

    def add_custom(self, key: str, material: Material) -> None:
        """Add a custom material to the in-memory database.

        Custom materials persist only for the lifetime of the process.

        Args:
            key: Unique identifier for the material. Must be a
                non-empty string.
            material: A Material instance to register.

        Raises:
            TypeError: If material is not a Material instance.
            ValueError: If key is empty or already exists as a
                built-in material.
        """
        if not isinstance(material, Material):
            raise TypeError(
                f"material must be a Material instance, "
                f"got {type(material).__name__}"
            )
        if not key or not isinstance(key, str):
            raise ValueError("key must be a non-empty string")

        normalized = key.lower()

        if normalized in self._builtin_keys:
            raise ValueError(
                f"Cannot overwrite built-in material '{key}'. "
                f"Built-in materials are read-only."
            )

        with self._lock:
            self._custom_materials[normalized] = material


def _dict_to_material(data: dict[str, Any]) -> Material:
    """Convert a raw data dict to a Material instance.

    Args:
        data: Dict with keys: name, conductivity, density,
            specific_heat, category, source.

    Returns:
        A frozen Material dataclass instance.
    """
    return Material(
        name=data["name"],
        conductivity=Q_(data["conductivity"], "W/(m*K)"),
        density=Q_(data["density"], "kg/m³"),
        specific_heat=Q_(data["specific_heat"], "J/(kg*K)"),
        category=data["category"],
        source=data["source"],
    )


# Module-level singleton — the one and only materials database.
_DB = MaterialsDB()
