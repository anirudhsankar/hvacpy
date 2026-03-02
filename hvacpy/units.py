"""Unit system wrapper around pint for hvacpy.

Every physical value in hvacpy carries its unit. This module provides
the thin wrapper so the pint API never leaks into user code.

Example:
    >>> from hvacpy import Q_
    >>> thickness = Q_(110, 'mm')
    >>> thickness.to('m')
    <Quantity(0.11, 'meter')>
"""

import pint

from hvacpy.exceptions import UnitError

# Single module-level registry — NOT the pint default registry.
_ureg = pint.UnitRegistry(auto_reduce_dimensions=False)

# Primary way users create dimensioned values.
Q_ = _ureg.Quantity

# Exposed so other hvacpy modules can access the registry for
# unit definitions (e.g. ureg.parse_units()).
ureg = _ureg


def validate_unit(
    qty: pint.Quantity,
    dimensionality: str,
    name: str,
) -> None:
    """Validate that a Quantity has the expected dimensionality.

    Args:
        qty: A pint Quantity to validate.
        dimensionality: Expected pint dimensionality string,
            e.g. '[length]' or '[length] * [mass] / [time]³ / [temperature]'.
        name: Human-readable name for the quantity, used in error
            messages. E.g. 'conductivity', 'thickness'.

    Returns:
        None.

    Raises:
        UnitError: If qty does not have the expected dimensionality.
    """
    if not qty.check(dimensionality):
        raise UnitError(
            f"'{name}' must have dimensionality {dimensionality}, "
            f"got {qty.dimensionality}"
        )
