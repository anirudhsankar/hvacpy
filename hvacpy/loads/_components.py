"""Component dataclasses for heat load calculations.

Data containers only — no calculations happen here. These describe
the building envelope and internal heat sources for a room or zone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from hvacpy.units import Q_

if TYPE_CHECKING:
    from pint import Quantity
    from hvacpy.assembly import Assembly


# ── Orientation Enum ────────────────────────────────────────────────

class Orientation(str, Enum):
    """Cardinal / inter-cardinal directions for building surfaces."""
    N  = "N"
    NE = "NE"
    E  = "E"
    SE = "SE"
    S  = "S"
    SW = "SW"
    W  = "W"
    NW = "NW"
    HORIZONTAL = "H"   # for roofs and skylights


# Valid wall groups per ASHRAE 1997 HOF Ch.28
_VALID_WALL_GROUPS = frozenset('ABCDEFG')

# Valid gain types
_VALID_GAIN_TYPES = frozenset({'people', 'lighting', 'equipment'})

# Valid activity types — keys of PEOPLE_SENSIBLE_W / PEOPLE_LATENT_W
_VALID_ACTIVITIES = frozenset({
    'seated_quiet', 'office_work', 'standing_light', 'walking',
    'light_bench_work', 'retail_banking', 'restaurant', 'dancing',
    'heavy_work',
})


# ── WallComponent ──────────────────────────────────────────────────

@dataclass
class WallComponent:
    """An opaque wall or roof surface contributing to cooling/heating load.

    Args:
        name:        Human label e.g. 'South facade'.
        assembly:    hvacpy Assembly — provides U-value.
        area:        Net wall area (excluding windows/doors) as Quantity (m² or ft²).
        orientation: Orientation enum value.
        wall_group:  ASHRAE CLTD wall group 'A' through 'G'. Default 'D'.
                     See _cltd_tables.py for group descriptions.
        is_roof:     True if this is a roof/ceiling surface. Default False.
    """
    name:        str
    assembly:    'Assembly'
    area:        'Quantity'
    orientation: Orientation
    wall_group:  str = 'D'
    is_roof:     bool = False

    def __post_init__(self) -> None:
        # Validate orientation is an Orientation enum member
        if not isinstance(self.orientation, Orientation):
            raise ValueError(
                f"orientation must be an Orientation enum value, "
                f"got {self.orientation!r}. Use e.g. Orientation.S"
            )
        # Validate wall_group
        wg = self.wall_group.upper()
        if wg not in _VALID_WALL_GROUPS:
            raise ValueError(
                f"wall_group must be one of {sorted(_VALID_WALL_GROUPS)} "
                f"('A' through 'G'), got {self.wall_group!r}"
            )
        self.wall_group = wg


# ── WindowComponent ────────────────────────────────────────────────

@dataclass
class WindowComponent:
    """A glazed opening contributing solar and conductive cooling load.

    Args:
        name:           Human label e.g. 'South glazing'.
        area:           Gross glazed area as Quantity (m² or ft²).
        orientation:    Orientation enum.
        u_factor:       Overall window U-factor as Quantity W/(m²K).
                        Typical double-glazed = 2.8, triple = 1.8.
        shgc:           Solar Heat Gain Coefficient 0.0–1.0.
                        Clear single = 0.87, Low-e double = 0.25–0.40.
        has_interior_shading: True if blinds/curtains present. Default False.
                        Affects CLF table selection.
        frame_fraction: Fraction of area that is frame (0.0–1.0). Default 0.15.
    """
    name:                 str
    area:                 'Quantity'
    orientation:          Orientation
    u_factor:             'Quantity'
    shgc:                 float
    has_interior_shading: bool = False
    frame_fraction:       float = 0.15

    def __post_init__(self) -> None:
        # Validate orientation
        if not isinstance(self.orientation, Orientation):
            raise ValueError(
                f"orientation must be an Orientation enum value, "
                f"got {self.orientation!r}. Use e.g. Orientation.S"
            )
        # Validate SHGC
        if not (0.0 <= self.shgc <= 1.0):
            raise ValueError(
                f"shgc must be between 0.0 and 1.0, got {self.shgc}"
            )
        # Validate frame_fraction
        if not (0.0 <= self.frame_fraction <= 0.5):
            raise ValueError(
                f"frame_fraction must be between 0.0 and 0.5, "
                f"got {self.frame_fraction}"
            )


# ── InternalGain ───────────────────────────────────────────────────

@dataclass
class InternalGain:
    """A heat source inside the space.

    For people: specify count and activity.
    For lighting: specify watts_per_m2 or total_watts.
    For equipment: specify watts_per_m2 or total_watts.
    """
    gain_type:      str          # 'people' | 'lighting' | 'equipment'
    # People fields
    count:          int   = 0
    activity:       str   = 'office_work'
    # Lighting / equipment fields
    watts_per_m2:   float = 0.0  # W/m² — used if total_watts is 0
    total_watts:    float = 0.0  # W — takes priority over watts_per_m2
    # Diversity factor
    diversity:      float = 1.0  # fraction of gain actually present (0.0–1.0)
    # CLF — cooling load factor accounting for thermal storage
    clf:            float = 1.0  # use 1.0 (conservative) unless specified

    def __post_init__(self) -> None:
        # Validate gain_type
        if self.gain_type not in _VALID_GAIN_TYPES:
            raise ValueError(
                f"gain_type must be one of {sorted(_VALID_GAIN_TYPES)}, "
                f"got {self.gain_type!r}"
            )
        # Validate activity for people
        if self.gain_type == 'people' and self.activity not in _VALID_ACTIVITIES:
            raise ValueError(
                f"Invalid activity {self.activity!r}. "
                f"Valid activities: {sorted(_VALID_ACTIVITIES)}"
            )
        # Validate diversity
        if not (0.0 <= self.diversity <= 1.0):
            raise ValueError(
                f"diversity must be between 0.0 and 1.0, "
                f"got {self.diversity}"
            )
