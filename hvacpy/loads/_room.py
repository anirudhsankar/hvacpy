"""Room and Zone dataclasses — space geometry and components.

No load calculations happen here. These are data containers that
describe the physical space and its envelope.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from hvacpy.units import Q_
from hvacpy.loads._components import WallComponent, WindowComponent, InternalGain

if TYPE_CHECKING:
    from pint import Quantity


@dataclass
class Room:
    """A single thermally-zoned space.

    Args:
        name:           Human label.
        floor_area:     Floor area as Quantity (m² or ft²).
        ceiling_height: Floor-to-ceiling height as Quantity (m or ft).
        walls:          List of WallComponent (opaque walls only).
        windows:        List of WindowComponent.
        internal_gains: List of InternalGain.
        ach_infiltration: Air changes per hour for infiltration. Default 0.5.
        t_indoor:       Indoor design temperature as Quantity. Default Q_(24,'degC').
    """
    name:             str
    floor_area:       'Quantity'
    ceiling_height:   'Quantity'
    walls:            list[WallComponent]      = field(default_factory=list)
    windows:          list[WindowComponent]    = field(default_factory=list)
    internal_gains:   list[InternalGain]       = field(default_factory=list)
    ach_infiltration: float                    = 0.5
    t_indoor:         'Quantity'               = field(default_factory=lambda: Q_(24, 'degC'))

    @property
    def volume_m3(self) -> float:
        """Room volume in m³ = floor_area * ceiling_height."""
        return (self.floor_area.to('m**2').magnitude *
                self.ceiling_height.to('m').magnitude)

    @property
    def floor_area_m2(self) -> float:
        """Floor area in m²."""
        return self.floor_area.to('m**2').magnitude


@dataclass
class Zone:
    """A collection of rooms served by a single HVAC system.

    The zone peak load is NOT the sum of room peaks —
    it is the peak of the sum of simultaneous room loads.
    This distinction is critical for equipment sizing.
    """
    name:  str
    rooms: list[Room] = field(default_factory=list)

    def add_room(self, room: Room) -> 'Zone':
        """Add a room to the zone. Returns self for chaining."""
        self.rooms.append(room)
        return self
