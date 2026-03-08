# hvacpy

**HVAC and building energy calculations for engineers.**

Free, open, practitioner-first Python tooling that replaces expensive
proprietary software and inherited Excel spreadsheets for everyday
HVAC engineering calculations.

[![PyPI](https://img.shields.io/pypi/v/hvacpy)](https://pypi.org/project/hvacpy/)
[![Python](https://img.shields.io/pypi/pyversions/hvacpy)](https://pypi.org/project/hvacpy/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

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
| **Equipment Sizing** | Split systems, RTUs, FCUs, chillers, heat pumps, duct sizing, ventilation |

## Quick Examples

**Wall U-value:**
```python
from hvacpy import Q_, Assembly

wall = Assembly("Brick Cavity Wall")
wall.add_layer("brick_common",      Q_(110, "mm"))
wall.add_layer("mineral_wool_batt", Q_(75, "mm"))
wall.add_layer("plasterboard_std",  Q_(12.5, "mm"))

print(wall.u_value)    # 0.347 W/(m²·K)
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
    Q_, Room, WallComponent, InternalGain, CoolingLoad, Orientation
)

room = Room(name="Office", floor_area=Q_(50, "m**2"),
            ceiling_height=Q_(3, "m"))
room.walls.append(WallComponent(
    name="South Wall", assembly=wall,
    area=Q_(20, "m**2"), orientation=Orientation.S,
))
room.internal_gains.append(
    InternalGain(gain_type="people", count=8, activity="office_work")
)

load = CoolingLoad(room, city="london")
print(f"Peak cooling: {load.peak_total.to('kW'):.2f}")
print(load.breakdown())
```

**Equipment sizing (v0.4):**
```python
from hvacpy import Q_, SplitSystem, DuctSizer, VentilationCheck

# Size a split system from the cooling load
ss = SplitSystem(load, cop_rated=3.5)
print(ss.summary())           # box-format sizing report
print(ss.nominal_capacity)    # e.g. 10.0 kW
print(ss.oversizing_warning)  # None / 'WARNING' / 'CRITICAL'

# Size a main supply duct — equal friction method
ds = DuctSizer(Q_(0.5, "m**3/s"), method="equal_friction")
print(ds.diameter)            # e.g. 400 mm standard size
print(ds.velocity)            # actual air velocity
print(ds.summary())           # Dia400mm - 3.98m/s - 0.45Pa/m - or 600x400mm rect

# Check ventilation compliance (ASHRAE 62.1-2022)
vc = VentilationCheck(room, supply_airflow=Q_(0.5, "m**3/s"), space_type="office")
print(vc.compliant)           # True / False
print(vc.summary())
```

## Design Principles

- **Correct before fast** — all equations trace to ASHRAE and ISO sources
- **Units everywhere** — every value carries its unit, no silent conversions
- **Practitioner language** — APIs use terms engineers actually use
- **The engineer always decides** — hvacpy calculates and warns; it never refuses

## Standards Referenced

| Standard | Used in |
|---|---|
| ASHRAE HOF 2021 Ch.28 | Cooling loads (CLTD/CLF) |
| ASHRAE HOF 2021 Ch.18 | Heating loads |
| ASHRAE HOF 2021 Ch.14 | Psychrometrics |
| ASHRAE HOF 2021 Ch.21 | Duct sizing |
| ASHRAE HSE 2020 | Equipment sizing |
| ASHRAE 62.1-2022 | Ventilation compliance |

## Test Coverage

185 tests · 92% equipment coverage · all verified against reference values

## Roadmap

- v0.5 — Weather data (EPW files, degree days, ASHRAE design conditions)
- v0.6 — Data centre loads (IT load, PUE, WUE, economiser analysis)
- v1.0 — Annual energy estimation and carbon footprint reporting

## License

MIT
