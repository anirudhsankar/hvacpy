Equipment Sizing
================

Equipment sizing (ASHRAE HSE 2020), duct sizing (ASHRAE HOF 2021 Ch.21),
and ventilation compliance (ASHRAE 62.1-2022).

Cooling Equipment
-----------------

.. autoclass:: hvacpy.equipment.SplitSystem
   :members:
   :show-inheritance:

.. autoclass:: hvacpy.equipment.PackagedRTU
   :members:
   :show-inheritance:

.. autoclass:: hvacpy.equipment.FanCoilUnit
   :members:
   :show-inheritance:

.. autoclass:: hvacpy.equipment.Chiller
   :members:
   :show-inheritance:

Heat Pump
---------

.. autoclass:: hvacpy.equipment.AirSourceHeatPump
   :members:
   :show-inheritance:

Duct Sizing
-----------

.. autoclass:: hvacpy.equipment.DuctSizer
   :members:
   :show-inheritance:

Ventilation
-----------

.. autoclass:: hvacpy.equipment.VentilationCheck
   :members:
   :show-inheritance:

Airflow Functions
-----------------

.. automodule:: hvacpy.equipment._airflow
   :members:

Convenience Functions
---------------------

.. autofunction:: hvacpy.equipment.size_cooling_equipment
.. autofunction:: hvacpy.equipment.size_heat_pump

Exceptions
----------

.. automodule:: hvacpy.exceptions
   :members:
   :show-inheritance:
