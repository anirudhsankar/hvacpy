"""AirProcess — models HVAC processes between two AirState objects.

An AirProcess connects two AirState objects (inlet and outlet) and
calculates the energy and mass flows involved in the process.

Example:
    >>> from hvacpy import Q_, AirState, AirProcess
    >>> s_in = AirState(dry_bulb=Q_(28, 'degC'), rh=0.65)
    >>> s_out = AirState(dry_bulb=Q_(13, 'degC'), rh=0.95)
    >>> proc = AirProcess(s_in, s_out, Q_(1, 'kg/s'))
    >>> print(proc.process_type)
    cooling_dehumidification
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pint import Quantity

from hvacpy.units import Q_
from hvacpy.psychrometrics._equations import CP_DA, H_FG_0

if TYPE_CHECKING:
    from hvacpy.psychrometrics import AirState


class AirProcess:
    """Represents an HVAC process between two air states.

    Args:
        state_in: Inlet AirState.
        state_out: Outlet AirState.
        mass_flow: Dry air mass flow rate as Quantity (kg/s or kg/h).

    Raises:
        TypeError: If arguments are not the expected types.
    """

    def __init__(
        self,
        state_in: "AirState",
        state_out: "AirState",
        mass_flow: Quantity,
    ) -> None:
        self._state_in = state_in
        self._state_out = state_out
        self._mass_flow_kg_s: float = mass_flow.to("kg/s").magnitude

        # Cache internal float values.
        self._t_db_in: float = state_in._t_db
        self._t_db_out: float = state_out._t_db
        self._W_in: float = state_in._W
        self._W_out: float = state_out._W
        self._h_in: float = state_in.enthalpy.magnitude
        self._h_out: float = state_out.enthalpy.magnitude

    @property
    def sensible_heat(self) -> Quantity:
        """Sensible heat transfer rate.

        = mass_flow * CP_DA * (t_db_out - t_db_in).
        Positive = heating, negative = cooling.

        Returns:
            Quantity: Sensible heat in W.
        """
        q_s = (
            self._mass_flow_kg_s
            * CP_DA
            * (self._t_db_out - self._t_db_in)
        )
        return Q_(q_s, "W")

    @property
    def latent_heat(self) -> Quantity:
        """Latent heat transfer rate.

        = mass_flow * H_FG_0 * (W_out - W_in).
        Positive = humidification, negative = dehumidification.

        Returns:
            Quantity: Latent heat in W.
        """
        q_l = (
            self._mass_flow_kg_s
            * H_FG_0
            * (self._W_out - self._W_in)
        )
        return Q_(q_l, "W")

    @property
    def total_heat(self) -> Quantity:
        """Total heat transfer rate.

        = mass_flow * (h_out - h_in).
        Sign follows enthalpy change.

        Returns:
            Quantity: Total heat in W.
        """
        q_t = (
            self._mass_flow_kg_s
            * (self._h_out - self._h_in)
        )
        return Q_(q_t, "W")

    @property
    def sensible_ratio(self) -> float:
        """Sensible Heat Ratio (SHR).

        = sensible_heat / total_heat. Between -1.0 and 1.0.

        Returns:
            float: SHR value.
        """
        total = self.total_heat.magnitude
        if abs(total) < 1e-10:
            return 1.0
        return self.sensible_heat.magnitude / total

    @property
    def moisture_added(self) -> Quantity:
        """Mass rate of moisture added or removed.

        = mass_flow * (W_out - W_in).
        Negative = dehumidification.

        Returns:
            Quantity: Moisture flow in kg/s.
        """
        dm = self._mass_flow_kg_s * (self._W_out - self._W_in)
        return Q_(dm, "kg/s")

    @property
    def process_type(self) -> str:
        """Classify the HVAC process.

        Returns:
            str: One of 'heating', 'cooling', 'humidification',
                'dehumidification', 'cooling_dehumidification',
                'heating_humidification', 'no_change'.
        """
        dt = self._t_db_out - self._t_db_in
        dW = self._W_out - self._W_in

        sensible_threshold = 0.01  # °C
        latent_threshold = 1e-6  # kg/kg

        is_heating = dt > sensible_threshold
        is_cooling = dt < -sensible_threshold
        is_humidifying = dW > latent_threshold
        is_dehumidifying = dW < -latent_threshold

        if is_heating and is_humidifying:
            return "heating_humidification"
        elif is_cooling and is_dehumidifying:
            return "cooling_dehumidification"
        elif is_heating and not is_humidifying and not is_dehumidifying:
            return "heating"
        elif is_cooling and not is_humidifying and not is_dehumidifying:
            return "cooling"
        elif is_humidifying and not is_heating and not is_cooling:
            return "humidification"
        elif is_dehumidifying and not is_heating and not is_cooling:
            return "dehumidification"
        else:
            return "no_change"
