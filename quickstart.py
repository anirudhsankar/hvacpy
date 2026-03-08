"""hvacpy quickstart — v0.4 verification script.

Covers all four modules: Assembly (v0.1), Psychrometrics (v0.2),
Heat Loads (v0.3), and Equipment Sizing (v0.4).
Run with:  python quickstart.py
"""

from hvacpy import (
    Q_, Assembly, db,
    Room, Zone, WallComponent, WindowComponent, InternalGain,
    CoolingLoad, HeatingLoad, Orientation,
    SplitSystem, PackagedRTU, AirSourceHeatPump,
    DuctSizer, VentilationCheck,
)

# ── v0.1 — Assembly (envelope) ──────────────────────────────────────

wall_assy = Assembly('Office South Wall')
wall_assy.add_layer('brick_common',      Q_(110, 'mm'))
wall_assy.add_layer('mineral_wool_batt', Q_(75,  'mm'))
wall_assy.add_layer('plasterboard_std',  Q_(12.5,'mm'))

roof_assy = Assembly('Flat Roof', orientation='roof')
roof_assy.add_layer('concrete_dense',  Q_(150, 'mm'))
roof_assy.add_layer('xps_insulation',  Q_(100, 'mm'))
roof_assy.add_layer('bitumen_felt',    Q_(5,   'mm'))

assert wall_assy.u_value.magnitude > 0

# ── v0.3 — Heat Loads ────────────────────────────────────────────────

room = Room(
    name='Open Plan Office',
    floor_area=Q_(100, 'm**2'),
    ceiling_height=Q_(3, 'm'),
    ach_infiltration=0.5,
)
room.walls.append(WallComponent(
    name='South Wall', assembly=wall_assy,
    area=Q_(30, 'm**2'), orientation=Orientation.S,
))
room.walls.append(WallComponent(
    name='Roof', assembly=roof_assy,
    area=Q_(100, 'm**2'), orientation=Orientation.HORIZONTAL, is_roof=True,
))
room.windows.append(WindowComponent(
    name='South Glazing', area=Q_(15, 'm**2'),
    orientation=Orientation.S, u_factor=Q_(2.8, 'W/(m**2*K)'),
    shgc=0.40,
))
room.internal_gains.append(InternalGain(gain_type='people', count=20, activity='office_work'))
room.internal_gains.append(InternalGain(gain_type='lighting', watts_per_m2=12))
room.internal_gains.append(InternalGain(gain_type='equipment', watts_per_m2=15))

cooling = CoolingLoad(room, city='london')
print(f"Peak cooling:  {cooling.peak_total.to('kW'):.2f}")
print(f"Peak hour:     {cooling.peak_hour}:00")
print(f"Sensible:      {cooling.peak_sensible.to('kW'):.2f}")
print(f"Latent:        {cooling.peak_latent.to('kW'):.2f}")
print(f"SHR:           {cooling.sensible_heat_ratio:.3f}")
print(cooling.breakdown())

heating = HeatingLoad(room, city='london')
print(f"Peak heating:  {heating.total.to('kW'):.2f}")
print(heating.breakdown())

# ── v0.4 — Equipment Sizing ─────────────────────────────────────────

print("\n" + "─" * 57)
print("EQUIPMENT SIZING (v0.4)")
print("─" * 57)

# Size a split system from the calculated cooling load
ss = SplitSystem(cooling, cop_rated=3.5)
print(f"\nSplit System:")
print(f"  Required:         {cooling.peak_total.to('kW'):.2f}")
print(f"  Selected nominal: {ss.nominal_capacity:.2f}")
print(f"  Oversizing ratio: {ss.oversizing_ratio:.3f}")
print(f"  Supply airflow:   {ss.supply_airflow.to('m**3/s'):.3f}")
print(f"  Warning:          {ss.oversizing_warning or 'None (within 25%)'}")
print(ss.summary())

# Size an air-source heat pump covering both modes
hp = AirSourceHeatPump(
    cooling, heating,
    t_outdoor_cooling=Q_(33, 'degC'),
    t_outdoor_heating=Q_(2, 'degC'),
)
print(f"\nAir-Source Heat Pump:")
print(f"  Nominal:           {hp.nominal_capacity_kw:.2f}")
print(f"  Binding mode:      {hp.binding_mode}")
print(f"  COP (cooling):     {hp.cop_at_design_cooling:.2f}")
print(f"  COP (heating):     {hp.cop_at_design_heating:.2f}")
print(f"  Heating coverage:  {hp.heating_coverage:.1%}")
print(f"  Supplemental heat: {hp.supplemental_heat_kw:.2f}" if hp.needs_supplemental_heat else "  Supplemental heat: Not required")
print(hp.summary())

# Size a supply duct with the equal friction method
supply_flow = ss.supply_airflow
ds = DuctSizer(supply_flow, method='equal_friction', section_type='main_supply')
print(f"\nDuct Sizing (equal friction, main supply):")
print(f"  Diameter:      {ds.diameter}")
print(f"  Velocity:      {ds.velocity:.2f}")
print(f"  Friction loss: {ds.friction_loss:.3f}")
print(f"  Velocity OK:   {ds.velocity_ok}")
print(f"  {ds.summary()}")

# Ventilation compliance (ASHRAE 62.1-2022)
vc = VentilationCheck(room, supply_airflow=supply_flow, space_type='office')
print(f"\nVentilation Compliance (ASHRAE 62.1-2022):")
print(f"  Required OA: {vc.required_oa_flow:.2f}")
print(f"  Actual OA:   {vc.actual_oa_flow:.2f}")
print(f"  Compliant:   {vc.compliant}")
print(f"  {vc.summary()}")

# ── Assertions ───────────────────────────────────────────────────────

assert cooling.peak_total.magnitude > 0
assert 12 <= cooling.peak_hour <= 18, f"peak_hour {cooling.peak_hour} not in [12,18]"
assert 0.60 <= cooling.sensible_heat_ratio <= 0.85
assert heating.total.magnitude > 0
assert ss.nominal_capacity.magnitude > 0
assert ss.oversizing_ratio >= 1.0
assert ds.diameter.magnitude > 0
assert ds.velocity.magnitude > 0
assert ds.friction_loss.magnitude > 0
assert hp.nominal_capacity_kw.magnitude > 0
assert hp.heating_coverage > 0
assert vc.required_oa_flow.magnitude > 0
assert vc.actual_oa_flow.magnitude > 0

print("\n✓ All quickstart assertions passed!")
