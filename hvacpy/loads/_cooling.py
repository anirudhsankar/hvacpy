"""Cooling load calculations using the ASHRAE CLTD/CLF method.

Implements ASHRAE 1997 HOF Chapter 28 simplified cooling load method.
This is the industry-standard method for preliminary and design-stage
cooling load calculations in commercial buildings.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from hvacpy.units import Q_
from hvacpy.exceptions import HvacpyError
from hvacpy.loads._components import WallComponent, WindowComponent, InternalGain, Orientation
from hvacpy.loads._cltd_tables import (
    get_cltd, get_clf_solar, get_i_max, get_design_conditions,
)
from hvacpy.loads._room import Room, Zone
from hvacpy.loads._internal import (
    calculate_people_gain, calculate_lighting_gain, calculate_equipment_gain,
)
from hvacpy.loads._infiltration import (
    calculate_infiltration_mass_flow,
    calculate_infiltration_sensible,
    calculate_infiltration_latent,
)

if TYPE_CHECKING:
    from pint import Quantity


# ── Design conditions reference — ASHRAE 1997 HOF Ch.28 ────────────
T_OUTDOOR_DESIGN_C   = 35.0    # °C — standard CLTD table base outdoor temp
T_INDOOR_DESIGN_C    = 24.0    # °C — standard CLTD table base indoor temp
DELTA_T_BASE         = 11.0    # K  — T_OUTDOOR_DESIGN - T_INDOOR_DESIGN

# Solar constants
SC_CLEAR_GLASS       = 1.0     # shading coefficient for clear single glass (reference)

# Internal gain factors — ASHRAE 1997 Table 3
PEOPLE_SENSIBLE_W = {
    'seated_quiet':      60,
    'office_work':       65,
    'standing_light':    70,
    'walking':           75,
    'light_bench_work':  80,
    'retail_banking':    75,
    'restaurant':        70,
    'dancing':          140,
    'heavy_work':       185,
}
PEOPLE_LATENT_W = {
    'seated_quiet':      45,
    'office_work':       55,
    'standing_light':    55,
    'walking':           55,
    'light_bench_work':  80,
    'retail_banking':    55,
    'restaurant':        80,
    'dancing':          175,
    'heavy_work':       250,
}


class CoolingLoad:
    """Calculates peak cooling load for a room or zone using CLTD/CLF method.

    Args:
        space:       Room or Zone to analyse.
        city:        City name string for design conditions lookup.
                     OR provide t_outdoor_db and t_outdoor_wb directly.
        t_outdoor_db: Outdoor design dry bulb temp as Quantity. Overrides city.
        t_outdoor_wb: Outdoor design wet bulb temp as Quantity. Overrides city.
        design_hour: Hour (1–24) at which to calculate load. Default: None
                     (calculates all 24 hours and returns peak).
        diurnal_range: Daily temp swing in K. Default Q_(10, 'delta_degC').
    """

    def __init__(
        self,
        space: Room | Zone,
        city: str | None = None,
        *,
        t_outdoor_db: 'Quantity | None' = None,
        t_outdoor_wb: 'Quantity | None' = None,
        design_hour:  int | None = None,
        diurnal_range: 'Quantity | None' = None,
    ) -> None:
        self._space = space
        self._design_hour = design_hour

        # Resolve design conditions
        if t_outdoor_db is not None:
            self._t_outdoor_db = t_outdoor_db.to('degC').magnitude
            self._t_outdoor_wb = (
                t_outdoor_wb.to('degC').magnitude if t_outdoor_wb is not None
                else self._t_outdoor_db - 5.0  # rough default
            )
        elif city is not None:
            dc = get_design_conditions(city)
            self._t_outdoor_db = dc['t_outdoor_db']
            self._t_outdoor_wb = dc['t_outdoor_wb']
        else:
            raise HvacpyError(
                "Must provide either 'city' or 't_outdoor_db' for cooling load."
            )

        # Diurnal range
        if diurnal_range is not None:
            self._diurnal_range = diurnal_range.to('delta_degC').magnitude
        else:
            self._diurnal_range = 10.0  # default

        # Get rooms list
        if isinstance(space, Zone):
            self._rooms = space.rooms
        else:
            self._rooms = [space]

        # Calculate all 24 hours
        self._hourly: dict[int, dict] = {}
        for hour in range(1, 25):
            self._hourly[hour] = self._calc_hour(hour)

        # Find peak hour
        if design_hour is not None:
            self._peak_hour = design_hour
        else:
            self._peak_hour = max(
                range(1, 25),
                key=lambda h: self._hourly[h]['total']
            )

    def _calc_hour(self, hour: int) -> dict:
        """Calculate all load components at a given hour."""
        wall_cond = 0.0
        window_cond = 0.0
        solar = 0.0
        inf_sensible = 0.0
        inf_latent = 0.0
        people_sens = 0.0
        people_lat = 0.0
        lighting = 0.0
        equip_sens = 0.0
        equip_lat = 0.0

        t_outdoor_db = self._t_outdoor_db
        diurnal = self._diurnal_range

        for room in self._rooms:
            t_indoor = room.t_indoor.to('degC').magnitude

            # Wall conduction — CLTD method (ASHRAE 1997 HOF Eq. 28-1)
            for wall in room.walls:
                u_val = wall.assembly.u_value.magnitude  # W/(m²K)
                area = wall.area.to('m**2').magnitude
                orient = wall.orientation.value

                # Look up CLTD
                if wall.is_roof:
                    cltd_table = get_cltd(hour, orient, 'G')
                else:
                    cltd_table = get_cltd(hour, orient, wall.wall_group)

                # CLTD correction — ASHRAE 1997 HOF
                # CLTD_corrected = CLTD_table + (25.5 - T_indoor)
                #                  + (T_outdoor_mean - 29.4)
                # T_outdoor_mean = T_outdoor_db - 0.5 * diurnal_range
                t_outdoor_mean = t_outdoor_db - 0.5 * diurnal
                cltd_corrected = (
                    cltd_table
                    + (25.5 - t_indoor)
                    + (t_outdoor_mean - 29.4)
                )

                # Q_wall = U * A * CLTD_corrected
                # CLTD_corrected can be negative — physically valid
                q = u_val * area * cltd_corrected
                wall_cond += q

            # Window conduction — instantaneous ΔT (no CLTD)
            for win in room.windows:
                u_win = win.u_factor.to('W/(m**2*K)').magnitude
                area_win = win.area.to('m**2').magnitude
                q_win_cond = u_win * area_win * (t_outdoor_db - t_indoor)
                window_cond += q_win_cond

                # Solar heat gain — ASHRAE 1997 HOF Eq. 28-3
                orient = win.orientation.value
                a_glazed = area_win * (1.0 - win.frame_fraction)
                shgc = win.shgc
                sc_ratio = shgc / 0.87  # normalise to clear single glass
                clf = get_clf_solar(hour, orient, win.has_interior_shading)
                i_max = get_i_max(orient)

                # Q_solar = A_glazed * SC_ratio * CLF * I_max
                # Note: we use SC_ratio (= SHGC/0.87) not SHGC directly.
                # The I_max values already incorporate the solar geometry.
                # This is a simplification for 32°N July — will be replaced
                # with full solar geometry in v0.5.
                q_solar = a_glazed * sc_ratio * clf * i_max
                solar += q_solar

            # Infiltration
            volume = room.volume_m3
            m_dot = calculate_infiltration_mass_flow(
                room.ach_infiltration, volume
            )
            inf_sensible += calculate_infiltration_sensible(
                m_dot, t_outdoor_db, t_indoor
            )
            inf_latent += calculate_infiltration_latent(m_dot)

            # Internal gains
            floor_area_m2 = room.floor_area_m2
            for gain in room.internal_gains:
                if gain.gain_type == 'people':
                    s, l = calculate_people_gain(
                        gain.count, gain.activity, gain.diversity, gain.clf
                    )
                    people_sens += s
                    people_lat += l
                elif gain.gain_type == 'lighting':
                    q_light = calculate_lighting_gain(
                        gain.total_watts, gain.watts_per_m2, floor_area_m2,
                        gain.diversity, gain.clf
                    )
                    lighting += q_light
                elif gain.gain_type == 'equipment':
                    s, l = calculate_equipment_gain(
                        gain.total_watts, gain.watts_per_m2, floor_area_m2,
                        gain.diversity, gain.clf
                    )
                    equip_sens += s
                    equip_lat += l

        sensible = (
            wall_cond + window_cond + solar + inf_sensible
            + people_sens + lighting + equip_sens
        )
        latent = inf_latent + people_lat + equip_lat
        total = sensible + latent

        return {
            'wall_conduction': wall_cond,
            'window_conduction': window_cond,
            'solar_gain': solar,
            'infiltration_sensible': inf_sensible,
            'infiltration_latent': inf_latent,
            'people_sensible': people_sens,
            'people_latent': people_lat,
            'lighting_gain': lighting,
            'equipment_sensible': equip_sens,
            'equipment_latent': equip_lat,
            'sensible': sensible,
            'latent': latent,
            'total': total,
        }

    # ── Properties — all return Quantities in Watts ─────────────────

    @property
    def peak_total(self) -> 'Quantity':
        """Sum of all sensible + latent at the peak hour."""
        return Q_(self._hourly[self._peak_hour]['total'], 'W')

    @property
    def peak_sensible(self) -> 'Quantity':
        """Sensible component at peak hour."""
        return Q_(self._hourly[self._peak_hour]['sensible'], 'W')

    @property
    def peak_latent(self) -> 'Quantity':
        """Latent component at peak hour = infiltration_latent + people_latent + equipment_latent."""
        return Q_(self._hourly[self._peak_hour]['latent'], 'W')

    @property
    def peak_hour(self) -> int:
        """Hour (1–24) at which peak_total occurs."""
        return self._peak_hour

    @property
    def wall_conduction(self) -> 'Quantity':
        """Total wall+roof conduction at peak hour."""
        return Q_(self._hourly[self._peak_hour]['wall_conduction'], 'W')

    @property
    def window_conduction(self) -> 'Quantity':
        """Total window conduction at peak hour."""
        return Q_(self._hourly[self._peak_hour]['window_conduction'], 'W')

    @property
    def solar_gain(self) -> 'Quantity':
        """Total solar heat gain at peak hour."""
        return Q_(self._hourly[self._peak_hour]['solar_gain'], 'W')

    @property
    def infiltration_sensible(self) -> 'Quantity':
        """Infiltration sensible at peak hour."""
        return Q_(self._hourly[self._peak_hour]['infiltration_sensible'], 'W')

    @property
    def infiltration_latent(self) -> 'Quantity':
        """Infiltration latent at peak hour."""
        return Q_(self._hourly[self._peak_hour]['infiltration_latent'], 'W')

    @property
    def people_sensible(self) -> 'Quantity':
        """People sensible at peak hour."""
        return Q_(self._hourly[self._peak_hour]['people_sensible'], 'W')

    @property
    def people_latent(self) -> 'Quantity':
        """People latent at peak hour."""
        return Q_(self._hourly[self._peak_hour]['people_latent'], 'W')

    @property
    def lighting_gain(self) -> 'Quantity':
        """Lighting gain (all sensible) at peak hour."""
        return Q_(self._hourly[self._peak_hour]['lighting_gain'], 'W')

    @property
    def equipment_sensible(self) -> 'Quantity':
        """Equipment sensible at peak hour."""
        return Q_(self._hourly[self._peak_hour]['equipment_sensible'], 'W')

    @property
    def equipment_latent(self) -> 'Quantity':
        """Equipment latent at peak hour."""
        return Q_(self._hourly[self._peak_hour]['equipment_latent'], 'W')

    @property
    def sensible_heat_ratio(self) -> float:
        """SHR = peak_sensible / peak_total."""
        total = self._hourly[self._peak_hour]['total']
        if total == 0:
            return 1.0
        return self._hourly[self._peak_hour]['sensible'] / total

    # ── Methods ─────────────────────────────────────────────────────

    def hourly_profile(self) -> dict[int, float]:
        """Returns dict of {hour: total_load_W} for all 24 hours.

        Useful for understanding load shape over the day.
        """
        return {h: data['total'] for h, data in self._hourly.items()}

    def breakdown(self) -> str:
        """Formatted table of all components, their W value, and % of peak_total.

        Same style as Assembly.breakdown().
        """
        data = self._hourly[self._peak_hour]
        total = data['total']

        def pct(val: float) -> str:
            if total == 0:
                return '  0.0%'
            return f'{val / total * 100:5.1f}%'

        lines: list[str] = []
        lines.append(f'Cooling Load Breakdown — Peak Hour {self._peak_hour}:00')
        lines.append('━' * 55)

        components = [
            ('Wall conduction',         data['wall_conduction']),
            ('Window conduction',       data['window_conduction']),
            ('Solar gain',              data['solar_gain']),
            ('Infiltration (sensible)', data['infiltration_sensible']),
            ('Infiltration (latent)',   data['infiltration_latent']),
            ('People (sensible)',       data['people_sensible']),
            ('People (latent)',         data['people_latent']),
            ('Lighting',                data['lighting_gain']),
            ('Equipment (sensible)',    data['equipment_sensible']),
            ('Equipment (latent)',      data['equipment_latent']),
        ]

        for label, val in components:
            lines.append(f'  {label:<26s} {val:>8.1f} W  {pct(val)}')

        lines.append('━' * 55)
        lines.append(f'  {"TOTAL SENSIBLE":<26s} {data["sensible"]:>8.1f} W  {pct(data["sensible"])}')
        lines.append(f'  {"TOTAL LATENT":<26s} {data["latent"]:>8.1f} W  {pct(data["latent"])}')
        lines.append(f'  {"PEAK TOTAL":<26s} {total:>8.1f} W  100.0%')
        lines.append(f'  SHR = {self.sensible_heat_ratio:.3f}')

        return '\n'.join(lines)

    def to_dict(self) -> dict:
        """All properties as plain floats in SI.

        Includes 'peak_hour', all component loads in W, 'shr'.
        """
        data = self._hourly[self._peak_hour]
        return {
            'peak_hour': self._peak_hour,
            'peak_total_W': data['total'],
            'peak_sensible_W': data['sensible'],
            'peak_latent_W': data['latent'],
            'wall_conduction_W': data['wall_conduction'],
            'window_conduction_W': data['window_conduction'],
            'solar_gain_W': data['solar_gain'],
            'infiltration_sensible_W': data['infiltration_sensible'],
            'infiltration_latent_W': data['infiltration_latent'],
            'people_sensible_W': data['people_sensible'],
            'people_latent_W': data['people_latent'],
            'lighting_gain_W': data['lighting_gain'],
            'equipment_sensible_W': data['equipment_sensible'],
            'equipment_latent_W': data['equipment_latent'],
            'shr': self.sensible_heat_ratio,
        }
