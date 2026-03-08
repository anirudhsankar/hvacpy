"""Custom exceptions for the hvacpy package.

All hvacpy-specific exceptions are defined here. No exceptions are
defined in any other module.
"""


class HvacpyError(Exception):
    """Base exception for all hvacpy errors."""


class UnitError(HvacpyError, ValueError):
    """Raised when a Quantity has an incompatible unit."""


class MaterialNotFoundError(HvacpyError, KeyError):
    """Raised when a material key is not in the database."""


class PsychrometricInputError(HvacpyError, ValueError):
    """Raised when psychrometric input properties are invalid."""


class LoadCalculationError(HvacpyError, ValueError):
    """Raised when a load calculation cannot be completed."""


class DesignConditionsNotFoundError(HvacpyError, KeyError):
    """Raised when a city is not in the design conditions database."""


class EquipmentSizingError(HvacpyError, ValueError):
    """Raised when load exceeds all available nominal sizes."""


class AirflowCalculationError(HvacpyError, ValueError):
    """Raised when airflow calculation has invalid inputs."""


class DuctSizingError(HvacpyError, ValueError):
    """Raised when duct sizing fails to converge."""
