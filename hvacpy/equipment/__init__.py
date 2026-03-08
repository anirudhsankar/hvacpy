"""hvacpy.equipment — Equipment Sizing (v0.4).

ASHRAE HSE 2020 equipment sizing, ASHRAE HOF 2021 Ch.21 duct sizing,
ASHRAE 62.1-2022 ventilation compliance.

Public API:
    SplitSystem, PackagedRTU, FanCoilUnit, Chiller
    AirSourceHeatPump
    DuctSizer
    VentilationCheck
    size_cooling_equipment, size_heat_pump (convenience functions)
"""

from hvacpy.equipment._cooling import (
    SplitSystem, PackagedRTU, FanCoilUnit, Chiller,
)
from hvacpy.equipment._heatpump import AirSourceHeatPump
from hvacpy.equipment._duct import DuctSizer
from hvacpy.equipment._ventilation import VentilationCheck
from hvacpy.equipment._airflow import (
    supply_airflow_cooling,
    supply_airflow_heating,
    airflow_from_cooling_load,
)
from hvacpy.equipment._nominal_sizes import next_size_up, NOMINAL_SIZES


def size_cooling_equipment(cooling_load, equipment_class=SplitSystem, **kwargs):
    """Convenience function to size cooling equipment from a CoolingLoad."""
    return equipment_class(cooling_load, **kwargs)


def size_heat_pump(cooling_load, heating_load, **kwargs):
    """Convenience function to size an air-source heat pump."""
    return AirSourceHeatPump(cooling_load, heating_load, **kwargs)


__all__ = [
    'SplitSystem', 'PackagedRTU', 'FanCoilUnit', 'Chiller',
    'AirSourceHeatPump',
    'DuctSizer',
    'VentilationCheck',
    'size_cooling_equipment', 'size_heat_pump',
    'supply_airflow_cooling', 'supply_airflow_heating',
    'airflow_from_cooling_load',
    'next_size_up', 'NOMINAL_SIZES',
]
