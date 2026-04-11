"""QCIO Structure interface."""

import pint
from automol import geometry_hash
from qcdata import Structure

from ..models import GeometryRow


def geometry_row(struc: Structure) -> GeometryRow:
    """
    Generate Geometry from QCIO Structure.

    Parameters
    ----------
    struc
        QCIO Structure.

    Returns
    -------
        GeometryRow
    """
    geo_row = GeometryRow(
        symbols=struc.symbols,
        coordinates=struc.geometry * pint.Quantity("bohr").m_as("angstrom"),
        charge=struc.charge,
        spin=struc.multiplicity - 1,
    )

    if geo_row.hash is None:
        geo_row.hash = geometry_hash(geo_row, decimals=6)

    return geo_row
