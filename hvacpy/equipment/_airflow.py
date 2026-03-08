"""Supply airflow pure functions.

Calculates required supply air volume flow rates from sensible loads.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from hvacpy.units import Q_
from hvacpy.exceptions import AirflowCalculationError

if TYPE_CHECKING:
    from pint import Quantity

# Physical constants
RHO_AIR = 1.2      # kg/m³ standard air density
CP_DA = 1006.0      # J/(kg·K) specific heat dry air


def supply_airflow_cooling(
    sensible_load: 'Quantity',
    t_room: 'Quantity | None' = None,
    t_supply: 'Quantity | None' = None,
) -> 'Quantity':
    """Calculate supply airflow for cooling from sensible load.

    V_dot = Q_sensible / (rho_air * CP_DA * (T_room - T_supply))

    Args:
        sensible_load: Sensible cooling load as Quantity (W).
        t_room: Room temperature. Default 24°C.
        t_supply: Supply air temperature. Default 13°C.

    Returns:
        Volume flow rate as Quantity (m³/s).

    Raises:
        AirflowCalculationError: If T_supply >= T_room.
    """
    if t_room is None:
        t_room = Q_(24, 'degC')
    if t_supply is None:
        t_supply = Q_(13, 'degC')

    t_room_c = t_room.to('degC').magnitude
    t_supply_c = t_supply.to('degC').magnitude
    delta_t = t_room_c - t_supply_c

    if delta_t <= 0:
        raise AirflowCalculationError(
            'Supply air temperature must be below room temperature for cooling.'
        )

    q_w = sensible_load.to('W').magnitude
    v_dot = q_w / (RHO_AIR * CP_DA * delta_t)
    return Q_(v_dot, 'm**3/s')


def supply_airflow_heating(
    heating_load: 'Quantity',
    t_room: 'Quantity | None' = None,
    t_supply: 'Quantity | None' = None,
) -> 'Quantity':
    """Calculate supply airflow for heating from heating load.

    V_dot = Q_heating / (rho_air * CP_DA * (T_supply - T_room))

    Args:
        heating_load: Heating load as Quantity (W).
        t_room: Room temperature. Default 21°C.
        t_supply: Supply air temperature. Default 40°C.

    Returns:
        Volume flow rate as Quantity (m³/s).
    """
    if t_room is None:
        t_room = Q_(21, 'degC')
    if t_supply is None:
        t_supply = Q_(40, 'degC')

    t_room_c = t_room.to('degC').magnitude
    t_supply_c = t_supply.to('degC').magnitude
    delta_t = t_supply_c - t_room_c

    if delta_t <= 0:
        raise AirflowCalculationError(
            'Supply air temperature must be above room temperature for heating.'
        )

    q_w = heating_load.to('W').magnitude
    v_dot = q_w / (RHO_AIR * CP_DA * delta_t)
    return Q_(v_dot, 'm**3/s')


def airflow_from_cooling_load(cooling_load, t_supply=None) -> 'Quantity':
    """Convenience wrapper — compute supply airflow from a CoolingLoad object.

    Uses peak_sensible and the room's indoor temperature.
    """
    sensible = cooling_load.peak_sensible

    # Try to get room temperature from the space
    t_room = Q_(24, 'degC')
    if hasattr(cooling_load, '_rooms') and cooling_load._rooms:
        t_room = cooling_load._rooms[0].t_indoor

    return supply_airflow_cooling(sensible, t_room=t_room, t_supply=t_supply)
