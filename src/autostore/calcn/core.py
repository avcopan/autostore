"""Calculation metadata."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from .util import CalculationDict, hash_from_dict, project_keywords


class Calculation(BaseModel):
    """Calculation input parameters and metadata."""

    # - Program Input -------
    program: str = Field(description="Quantum chemistry program used (psi4, ORCA, ...)")
    calctype: str = Field(description="Calculation type (energy, optimization, ...)")
    method: str = Field(description="Computational method (B3LYP, MP2, ...)")
    basis: str | None = Field(default=None, description="Basis set.")
    keywords: dict[str, str | dict | None] = Field(
        default_factory=dict, description="Quantum chemistry program keywords."
    )
    cmdline_args: list[str] = Field(
        default_factory=list, description="Command line arguments."
    )
    input: str | None = Field(default=None, description="Input file.")
    files: dict[str, str] = Field(
        default_factory=dict, description="Additional input files."
    )
    # - SuperProgram Input --
    superprogram: str | None = Field(
        default=None, description="Geometry optimizer program used (geomeTRIC, ...)"
    )
    superprogram_keywords: dict[str, str | dict | None] = Field(
        default_factory=dict, description="Geometry optimizer keywords."
    )
    # - Provenance ----------
    program_version: str | None = Field(default=None, description="Program version.")
    superprogram_version: str | None = Field(
        default=None, description="Superprogram version, if applicable."
    )
    scratch_dir: Path | None = Field(default=None, description="Working directory.")
    wall_time: float | None = Field(default=None, description="Wall time.")
    hostname: str | None = Field(default=None, description="Name of host machine.")
    hostcpus: int | None = Field(
        default=None, description="Number of CPUs on host machine."
    )
    hostmem: int | None = Field(
        default=None, description="Amount of memory on host machine."
    )
    extras: dict[str, str | dict | None] = Field(
        default_factory=dict, description="Additional metadata."
    )


def projected_hash(calc: Calculation, template: Calculation | CalculationDict) -> str:
    """
    Project calculation onto template and generate hash.

    Parameters
    ----------
    calc
        Calculation metadata.
    template
        Calculation metadata template.

    Returns
    -------
        Hash string.
    """
    calc_dct = project(calc, template)
    return hash_from_dict(calc_dct)


def project(
    calc: Calculation, template: Calculation | CalculationDict
) -> CalculationDict:
    """
    Project calculation onto template.

    Parameters
    ----------
    calc
        Calculation metadata.
    template
        Calculation metadata template.

    Returns
    -------
        Projected calculation dictionary.
    """
    # Dump template to dictionary
    template = (
        template.model_dump(exclude_unset=True)
        if isinstance(template, Calculation)
        else template
    )
    # Include only keywords and extras from template
    if "keywords" in template:
        calc.keywords = project_keywords(
            calc.keywords, template=template.get("keywords", {})
        )
    if "extras" in template:
        calc.extras = project_keywords(calc.extras, template=template.get("extras", {}))
    # Include only fields from template
    return calc.model_dump(exclude_none=True, include=set(template.keys()))
