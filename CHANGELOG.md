# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.3.0] — 2026-03-02

### Added
- **Heat Load Calculations** — ASHRAE CLTD/CLF cooling load method (1997 HOF Ch.28)
- **Heating Loads** — ASHRAE steady-state heat loss method (2021 HOF Ch.18)
- `CoolingLoad` — 24-hour peak cooling load with component breakdown
- `HeatingLoad` — steady-state heating for equipment sizing
- `Room` and `Zone` dataclasses for space modelling
- `WallComponent`, `WindowComponent`, `InternalGain` data containers
- `Orientation` enum (N, NE, E, SE, S, SW, W, NW, Horizontal)
- CLTD Group D lookup table (24h × 9 orientations) with group multipliers A–G
- CLF solar gain table with linear interpolation
- Design conditions database for 10 cities worldwide
- `LoadCalculationError` and `DesignConditionsNotFoundError` exceptions
- `scipy>=1.10` dependency (for future infiltration crack method)
- 56 new tests (120 total), 97% coverage on loads module

## [0.2.0] — 2026-03-01

### Added
- **Psychrometrics Module** — ASHRAE HOF 2021 moist air calculations
- `AirState` — compute all psychrometric properties from any two known values
- `AirProcess` — model mixing, heating, cooling, humidification processes
- `PsychChart` — matplotlib psychrometric chart plotting
- Convenience functions: `dry_bulb_from_wet_bulb`, `humidity_ratio_from_rh`, `dew_point_from_humidity_ratio`

## [0.1.0] — 2026-02-28

### Added
- **Assembly Module** — layered building envelope U-value/R-value calculations
- **Materials Database** — 15+ common construction materials with thermal properties
- `Assembly` class with `add_layer()`, `u_value`, `r_value`, `breakdown()`
- `Material` and `MaterialsDB` classes
- Unit system (`Q_`, `ureg`) powered by pint
- 64 unit tests
