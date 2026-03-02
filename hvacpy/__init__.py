"""hvacpy — HVAC and building energy calculations for engineers.

This package provides tools for building envelope thermal analysis,
including material properties, assembly U-value/R-value calculations,
and unit-aware engineering quantities.

Example:
    >>> from hvacpy import Q_, db, Assembly
    >>> wall = Assembly('My Wall')
    >>> wall.add_layer('brick_common', Q_(110, 'mm'))
    >>> wall.add_layer('mineral_wool_batt', Q_(100, 'mm'))
    >>> wall.add_layer('plasterboard_std', Q_(12.5, 'mm'))
    >>> print(wall.u_value)
    0.298... W / K / m²
"""

from hvacpy.units import Q_, ureg, validate_unit
from hvacpy.exceptions import UnitError, MaterialNotFoundError
from hvacpy.exceptions import PsychrometricInputError
from hvacpy.exceptions import LoadCalculationError, DesignConditionsNotFoundError
from hvacpy.materials import Material, MaterialsDB, _DB as db
from hvacpy.assembly import Assembly
from hvacpy.psychrometrics import AirState, PsychChart, AirProcess
from hvacpy.psychrometrics import (
    dry_bulb_from_wet_bulb,
    humidity_ratio_from_rh,
    dew_point_from_humidity_ratio,
)
from hvacpy.loads import CoolingLoad, HeatingLoad, Room, Zone
from hvacpy.loads import (
    WallComponent as Wall,
    WallComponent,
    WindowComponent as Window,
    WindowComponent,
    InternalGain,
    Orientation,
)

# Aliases for spec compatibility
Roof = WallComponent   # Roof is a WallComponent with is_roof=True
Floor = WallComponent  # Floor is a WallComponent (simplified for v0.3)
Wall = WallComponent
Window = WindowComponent

__version__ = '0.3.0'
__all__ = [
    'Q_', 'ureg', 'validate_unit',
    'UnitError', 'MaterialNotFoundError', 'PsychrometricInputError',
    'LoadCalculationError', 'DesignConditionsNotFoundError',
    'Material', 'MaterialsDB', 'db',
    'Assembly',
    'AirState', 'PsychChart', 'AirProcess',
    'dry_bulb_from_wet_bulb',
    'humidity_ratio_from_rh',
    'dew_point_from_humidity_ratio',
    'CoolingLoad', 'HeatingLoad', 'Room', 'Zone',
    'WallComponent', 'WindowComponent', 'InternalGain',
    'Orientation', 'Wall', 'Window', 'Roof', 'Floor',
    '__version__',
]
