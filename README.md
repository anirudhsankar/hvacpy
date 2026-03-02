# hvacpy

**HVAC and building energy calculations for engineers.**

Free, open, practitioner-first Python tooling that replaces expensive 
proprietary software and inherited Excel spreadsheets for everyday 
HVAC engineering calculations.

## Installation
```bash
pip install hvacpy
```

## What It Does

| Module | What you can calculate |
|--------|----------------------|
| **Assembly** | U-values and R-values for any wall, roof, or floor construction |
| **Psychrometrics** | All moist air properties from any two known conditions |
| **Heat Loads** | Cooling and heating loads for rooms and zones (CLTD/CLF method) |

## Quick Examples

**Wall U-value:**
```python
from hvacpy import Q_, Assembly

wall = Assembly("Brick Cavity Wall")
wall.add_layer("brick_common",     Q_(110, "mm"))
wall.add_layer("mineral_wool_batt", Q_(75, "mm"))
wall.add_layer("plasterboard_std",  Q_(12.5, "mm"))

print(wall.u_value)    # 0.347 W/(m²·K)
print(wall.breakdown())
```

**Moist air properties:**
```python
from hvacpy import Q_, AirState

air = AirState(dry_bulb=Q_(25, "degC"), rh=0.60)
print(air.wet_bulb)    # 19.47 °C
print(air.dew_point)   # 16.70 °C
print(air.enthalpy)    # 55.45 kJ/kg
```

**Cooling load:**
```python
from hvacpy import (
    Q_, Assembly, Room, WallComponent, WindowComponent,
    InternalGain, CoolingLoad, Orientation
)

room = Room(name="Office", floor_area=Q_(50, "m²"), 
            ceiling_height=Q_(3, "m"))
room.walls.append(WallComponent(
    name="South Wall", assembly=wall,
    area=Q_(20, "m²"), orientation=Orientation.S
))
room.internal_gains.append(
    InternalGain(gain_type="people", count=8, activity="office_work")
)

load = CoolingLoad(room, city="london")
print(f"Peak cooling: {load.peak_total.to('kW'):.2f}")
print(f"Peak hour:    {load.peak_hour}:00")
print(load.breakdown())
```

## Design Principles

- **Correct before fast** — all equations trace to ASHRAE and ISO sources
- **Units everywhere** — every value carries its unit, no silent conversions
- **Practitioner language** — APIs use terms engineers actually use
- **Tested** — 120 tests, 97% coverage, all verified against reference values

## Roadmap

- v0.4 — Equipment sizing (cooling units, AHUs, duct sizing)
- v0.5 — Weather data (EPW files, degree days, design conditions)
- v0.6 — Data centre loads (IT load, PUE, WUE, economiser analysis)
- v1.0 — Annual energy estimation and carbon footprint reporting

## License

MIT