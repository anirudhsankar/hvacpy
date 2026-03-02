"""hvacpy v0.3 quickstart verification script."""

from hvacpy import (
    Q_, Assembly, db,
    Room, Zone, WallComponent, WindowComponent, InternalGain,
    CoolingLoad, HeatingLoad, Orientation
)

# Build envelope
wall_assy = Assembly('Office South Wall')
wall_assy.add_layer('brick_common',   Q_(110, 'mm'))
wall_assy.add_layer('mineral_wool_batt', Q_(75, 'mm'))
wall_assy.add_layer('plasterboard_std',  Q_(12.5, 'mm'))

roof_assy = Assembly('Flat Roof', orientation='roof')
roof_assy.add_layer('concrete_dense',  Q_(150, 'mm'))
roof_assy.add_layer('xps_insulation',  Q_(100, 'mm'))
roof_assy.add_layer('bitumen_felt',     Q_(5, 'mm'))

# Build room
room = Room(
    name='Open Plan Office',
    floor_area=Q_(100, 'm**2'),
    ceiling_height=Q_(3, 'm'),
    ach_infiltration=0.5,
)
room.walls.append(WallComponent(
    name='South Wall', assembly=wall_assy,
    area=Q_(30, 'm**2'), orientation=Orientation.S
))
room.walls.append(WallComponent(
    name='Roof', assembly=roof_assy,
    area=Q_(100, 'm**2'), orientation=Orientation.HORIZONTAL, is_roof=True
))
room.windows.append(WindowComponent(
    name='South Glazing', area=Q_(15, 'm**2'),
    orientation=Orientation.S, u_factor=Q_(2.8, 'W/(m**2*K)'),
    shgc=0.40,
))
room.internal_gains.append(
    InternalGain(gain_type='people', count=20, activity='office_work')
)
room.internal_gains.append(
    InternalGain(gain_type='lighting', watts_per_m2=12)
)
room.internal_gains.append(
    InternalGain(gain_type='equipment', watts_per_m2=15)
)

# Cooling load
cooling = CoolingLoad(room, city='london')
print(f"Peak cooling:  {cooling.peak_total.to('kW'):.2f}")
print(f"Peak hour:     {cooling.peak_hour}:00")
print(f"Sensible:      {cooling.peak_sensible.to('kW'):.2f}")
print(f"Latent:        {cooling.peak_latent.to('kW'):.2f}")
print(f"SHR:           {cooling.sensible_heat_ratio:.3f}")
print(cooling.breakdown())
print()

# Heating load
heating = HeatingLoad(room, city='london')
print(f"Peak heating:  {heating.total.to('kW'):.2f}")
print(heating.breakdown())

# Validation assertions from spec Section 13
assert cooling.peak_total.magnitude > 0, "peak_total must be > 0"
assert 12 <= cooling.peak_hour <= 18, f"peak_hour {cooling.peak_hour} not in [12,18]"
assert 0.60 <= cooling.sensible_heat_ratio <= 0.85, f"SHR {cooling.sensible_heat_ratio:.3f} not in [0.60,0.85]"
assert heating.total.magnitude > 0, "heating total must be > 0"
assert heating.total.magnitude > heating.envelope_loss.magnitude, "heating total must be > envelope loss alone"

print("\n✓ All quickstart assertions passed!")
