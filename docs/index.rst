hvacpy Documentation
====================

**HVAC and building energy calculations for engineers.**

Free, open, practitioner-first Python tooling that replaces expensive
proprietary software for everyday HVAC engineering calculations.

.. code-block:: bash

   pip install hvacpy

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   quickstart
   modules/assembly
   modules/psychrometrics
   modules/loads
   modules/equipment

.. toctree::
   :maxdepth: 1
   :caption: Project

   changelog

Overview
--------

.. list-table::
   :header-rows: 1
   :widths: 20 40 20

   * - Module
     - What you can calculate
     - Since
   * - **Assembly**
     - U-values and R-values for any wall, roof, or floor construction
     - v0.1
   * - **Psychrometrics**
     - All moist air properties from any two known conditions
     - v0.2
   * - **Heat Loads**
     - Cooling and heating loads for rooms and zones (CLTD/CLF method)
     - v0.3
   * - **Equipment Sizing**
     - Split systems, RTUs, FCUs, chillers, heat pumps, duct sizing, ventilation
     - v0.4

Design Principles
-----------------

- **Correct before fast** — all equations trace to ASHRAE and ISO sources
- **Units everywhere** — every value carries its unit, no silent conversions
- **Practitioner language** — APIs use terms engineers actually use
- **The engineer always decides** — hvacpy calculates and warns; it never refuses
