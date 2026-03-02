"""Unit tests for hvacpy/materials/ — Tests M-01 through M-07."""

import pytest

from hvacpy import Q_, db
from hvacpy.materials import Material
from hvacpy.exceptions import MaterialNotFoundError


class TestMaterialGet:
    """TEST M-01, M-02, M-03 — get() method."""

    def test_m01_get_exact_match(self) -> None:
        """M-01: Get material by exact key."""
        mat = db.get("brick_common")
        assert abs(mat.conductivity.magnitude - 0.72) < 0.001
        assert abs(mat.density.magnitude - 1920) < 0.001

    def test_m02_get_case_insensitive(self) -> None:
        """M-02: Keys are case-insensitive."""
        upper = db.get("BRICK_COMMON")
        mixed = db.get("Brick_Common")
        lower = db.get("brick_common")
        assert upper == lower
        assert mixed == lower

    def test_m03_get_not_found(self) -> None:
        """M-03: Unknown key raises MaterialNotFoundError."""
        with pytest.raises(MaterialNotFoundError) as exc_info:
            db.get("unobtanium")
        msg = str(exc_info.value)
        assert "unobtanium" in msg
        assert "list_keys()" in msg


class TestMaterialListKeys:
    """TEST M-04 — list_keys()."""

    def test_m04_list_keys_sorted(self) -> None:
        """M-04: list_keys returns sorted list of 31 strings."""
        keys = db.list_keys()
        assert isinstance(keys, list)
        # 31 built-in materials (custom materials from other tests
        # may add more, so check >= 31).
        assert len(keys) >= 31
        assert keys[0] == "air_cavity_25mm"
        # Verify sorted.
        assert keys == sorted(keys)


class TestMaterialListByCategory:
    """TEST M-05 — list_by_category()."""

    def test_m05_filter_insulation(self) -> None:
        """M-05: Filtering by 'insulation' returns 7 materials."""
        materials = db.list_by_category("insulation")
        assert len(materials) == 7
        for mat in materials:
            assert mat.category == "insulation"

    def test_invalid_category_raises(self) -> None:
        """Invalid category raises ValueError."""
        with pytest.raises(ValueError):
            db.list_by_category("unobtainium_category")


class TestMaterialAddCustom:
    """TEST M-06, M-07 — add_custom()."""

    def test_m06_add_custom_success(self) -> None:
        """M-06: Adding a custom material works."""
        custom = Material(
            name="My Foam",
            conductivity=Q_(0.031, "W/(m*K)"),
            density=Q_(28, "kg/m³"),
            specific_heat=Q_(1400, "J/(kg*K)"),
            category="insulation",
            source="manufacturer",
        )
        db.add_custom("my_foam", custom)
        retrieved = db.get("my_foam")
        assert retrieved.conductivity.magnitude == 0.031

    def test_m07_cannot_overwrite_builtin(self) -> None:
        """M-07: Cannot overwrite a built-in material."""
        custom = Material(
            name="Fake Brick",
            conductivity=Q_(0.5, "W/(m*K)"),
            density=Q_(1000, "kg/m³"),
            specific_heat=Q_(800, "J/(kg*K)"),
            category="masonry",
            source="test",
        )
        with pytest.raises(ValueError) as exc_info:
            db.add_custom("brick_common", custom)
        msg = str(exc_info.value)
        assert "brick_common" in msg
        assert "built-in" in msg.lower()

    def test_add_custom_type_check(self) -> None:
        """add_custom rejects non-Material objects."""
        with pytest.raises(TypeError):
            db.add_custom("bad_material", {"name": "bad"})  # type: ignore
