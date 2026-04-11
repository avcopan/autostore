"""Calculation row model and associated models and functions."""

from pathlib import Path

from automol import Geometry, geom
from automol.types import FloatArray
from pydantic import ConfigDict
from sqlalchemy import event
from sqlalchemy.types import JSON, String
from sqlmodel import Column, Field, Relationship, Session, SQLModel, select

from .calcn import Calculation, calculation_hash, hash_registry
from .types import (
    FloatArrayTypeDecorator,
    PathTypeDecorator,
    Role,
    RowID,
)


# --- Link Models -------------------------------
class CalculationGeometryLink(SQLModel, table=True):
    """
    Link CalculationRows to GeometryRows.

    Attributes
    ----------
    geometry_id
        Foreign key to the linked geometry.
    calculation_id
        Foreign key to the linked geometry.
    role
        Role of the geometry in the calculation.
    """

    # - SQL Metadata --------
    __tablename__ = "calculation_geometry_link"
    model_config = ConfigDict(use_enum_values=True)
    # - Row id --------------
    # - Foreign keys --------
    geometry_id: RowID = Field(
        foreign_key="geometry.id",
        primary_key=True,
        ondelete="CASCADE",
        description="Foreign key to the linked geometry.",
    )
    calculation_id: RowID = Field(
        foreign_key="calculation.id",
        primary_key=True,
        ondelete="CASCADE",
        description="Foreign key to the linked geometry.",
    )
    # - Attributes ----------
    role: Role = Field(description="Role of the geometry in the calculation.")
    # - Linked table --------
    # - Linked tables -------


class StationaryIdentityLink(SQLModel, table=True):
    """Link StationaryPointRows to IdentityRows."""

    # - SQL Metadata --------
    __tablename__ = "stationary_identity_link"
    # - Row id --------------
    # - Foreign keys --------
    stationary_id: RowID = Field(
        foreign_key="stationary_point.id",
        primary_key=True,
        ondelete="CASCADE",
        description="Foreign key to the linked stationary point.",
    )
    identity_id: RowID = Field(
        foreign_key="identity.id",
        primary_key=True,
        ondelete="CASCADE",
        description="Foreign key to the linked identity.",
    )
    # - Attributes ----------
    # - Linked table --------
    # - Linked tables -------


class StationaryStageLink(SQLModel, table=True):
    """Link StationaryPointRows to StageRows."""

    # - SQL Metadata --------
    __tablename__ = "stationary_stage_link"
    # - Row id --------------
    # - Foreign keys --------
    stationary_id: RowID = Field(
        foreign_key="stationary_point.id",
        primary_key=True,
        ondelete="CASCADE",
        description="Foreign key to the linked stationary point.",
    )
    stage_id: RowID = Field(
        foreign_key="stage.id",
        primary_key=True,
        ondelete="CASCADE",
        description="Foreign key to the linked reaction stage.",
    )
    # - Attributes ----------
    # - Linked table --------
    # - Linked tables -------


# --- Calculation Models ------------------------
class CalculationRow(Calculation, SQLModel, table=True):
    """Calculation input parameters and metadata."""

    # - SQL Metadata --------
    __tablename__ = "calculation"
    # - Row id --------------
    id: RowID | None = Field(default=None, primary_key=True)
    # - Foreign keys --------
    # Have to redeclare these fields for sql type verification.
    # - Program Input -------
    program: str = Field(description="Quantum chemistry program used (psi4, ORCA, ...)")
    calctype: str = Field(description="Calculation type (energy, optimization, ...)")
    method: str = Field(description="Computational method (B3LYP, MP2, ...)")
    basis: str | None = Field(default=None, description="Basis set.")
    keywords: dict[str, str | dict | None] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Quantum chemistry program keywords.",
    )
    cmdline_args: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="Command line arguments.",
    )
    input: str | None = Field(default=None, description="Input file.")
    files: dict[str, str] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Additional input files.",
    )
    # - SuperProgram Input --
    superprogram: str | None = Field(
        default=None, description="Geometry optimizer program used (geomeTRIC, ...)"
    )
    superprogram_keywords: dict[str, str | dict | None] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Geometry optimizer keywords.",
    )
    # - Provenance ----------
    program_version: str | None = Field(default=None, description="Program version.")
    superprogram_version: str | None = Field(
        default=None, description="Superprogram version, if applicable."
    )
    scratch_dir: Path | None = Field(
        default=None,
        sa_column=Column(PathTypeDecorator),
        description="Working directory.",
    )
    wall_time: float | None = Field(default=None, description="Wall time.")
    hostname: str | None = Field(default=None, description="Name of host machine.")
    hostcpus: int | None = Field(
        default=None, description="Number of CPUs on host machine."
    )
    hostmem: int | None = Field(
        default=None, description="Amount of memory on host machine."
    )
    extras: dict[str, str | dict | None] = Field(
        default_factory=dict, sa_column=Column(JSON), description="Additional metadata."
    )
    # - Linked table --------
    # - Linked tables -------
    geometries: list["GeometryRow"] = Relationship(
        back_populates="calculations", link_model=CalculationGeometryLink
    )
    energies: list["EnergyRow"] = Relationship(
        back_populates="calculation", cascade_delete=True
    )
    hashes: list["CalculationHashRow"] = Relationship(
        back_populates="calculation", cascade_delete=True
    )
    stationary_points: list["StationaryPointRow"] = Relationship(
        back_populates="calculation"
    )


class CalculationHashRow(SQLModel, table=True):
    """Hash value for a calculation."""

    # - SQL Metadata --------
    __tablename__ = "calculation_hash"
    # - Row id --------------
    id: RowID | None = Field(default=None, primary_key=True)
    # - Foreign keys --------
    calculation_id: RowID = Field(
        foreign_key="calculation.id",
        index=True,
        nullable=False,
        ondelete="CASCADE",
        description="Foreign key to the linked geometry.",
    )
    # - Attributes ----------
    name: str = Field(
        index=True, description="Type of CalculationRow hash (minimal, full, ...)"
    )
    value: str = Field(
        sa_column=Column(String(64), index=True, nullable=False),
        description="Value of CalculationRow hash.",
    )
    # - Linked table --------
    calculation: CalculationRow = Relationship(back_populates="hashes")
    # - Linked tables -------


# --- Geometry Models ---------------------------
class GeometryRow(Geometry, SQLModel, table=True):
    """Molecular geometry."""

    # - SQL Metadata --------
    __tablename__ = "geometry"
    model_config = ConfigDict(arbitrary_types_allowed=True)
    # - Row id --------------
    id: RowID | None = Field(default=None, primary_key=True)
    # - Foreign keys --------
    # - Attributes ----------
    symbols: list[str] = Field(
        sa_column=Column(JSON), description="Atomic symbols in order."
    )
    coordinates: FloatArray = Field(
        sa_column=Column(FloatArrayTypeDecorator),
        description="Cartesian coordinates of atoms in Angstrom.",
    )
    charge: int = Field(default=0, description="Total molecular charge.")
    spin: int = Field(default=0, description="Number of unpaired electrons.")
    hash: str | None = Field(
        default=None,
        sa_column=Column(String(64), index=True, nullable=True, unique=True),
    )
    # ^ Populated by event listener
    # - Linked table --------
    stationary_point: "StationaryPointRow" = Relationship(back_populates="geometry")
    # - Linked tables -------
    calculations: list["CalculationRow"] = Relationship(
        back_populates="geometries", link_model=CalculationGeometryLink
    )
    energies: list["EnergyRow"] = Relationship(
        back_populates="geometry", cascade_delete=True
    )

    # Validate coordinates shape with a field validator:
    #    @field_validator("coordinates")
    #    @classmethod
    #    def validate_shape(cls, v):
    #        if not all(len(row) == 3 for row in v):
    #            raise ValueError("Coordinates must be shape (N, 3)")  # noqa: ERA001
    #        return v  # noqa: ERA001

    # Add formula field for indexing:
    #    formula: str = Field(sa_column=Column(String, nullable=False, index=True))  # noqa: E501, ERA001

    # Define symbols -> formula conversion function:
    #    def formula_from_symbols(symbols: list[str]) -> str

    # Attach SQLAlchemy event listener to auto-set formula on insert:
    #     from sqlalchemy import event  # noqa: ERA001
    #     @event.listens_for(GeometryRow, "before_insert")
    #     @event.listens_for(GeometryRow, "before_update")
    #     def populate_formula(mapper, connection, target: GeometryRow):
    #         target.formula = formula_from_symbols(target.symbols)  # noqa: ERA001
    # This will implement the symbol-formula sync at the ORM level, so that they
    # automatically stay in sync with any inserts or updates.


# --- Data Models -------------------------------
class EnergyRow(SQLModel, table=True):
    """Energy calculation results."""

    # - SQL Metadata --------
    __tablename__ = "energy"
    # - Row id --------------
    id: RowID | None = Field(default=None, primary_key=True)
    # - Foreign keys --------
    geometry_id: RowID | None = Field(
        default=None,
        foreign_key="geometry.id",
        ondelete="CASCADE",
        description="Foreign key to the linked geometry.",
    )
    calculation_id: RowID | None = Field(
        default=None,
        foreign_key="calculation.id",
        ondelete="CASCADE",
        description="Foreign key to the linked calculation.",
    )
    # - Attributes ----------
    value: float = Field(description="Energy in Hartree.")
    # - Linked table --------
    calculation: CalculationRow = Relationship(back_populates="energies")
    geometry: GeometryRow = Relationship(back_populates="energies")
    # - Linked tables -------


# --- Stationary Models -------------------------
class StationaryPointRow(SQLModel, table=True):
    """Stationary point geometries."""

    # - SQL Metadata --------
    __tablename__ = "stationary_point"
    # - Row id --------------
    id: RowID | None = Field(default=None, primary_key=True)
    # - Foreign keys --------
    geometry_id: RowID = Field(
        foreign_key="geometry.id",
        description="Foreign key to the linked geometry.",
    )
    calculation_id: RowID = Field(
        foreign_key="calculation.id",
        description="Foreign key to the linked calculation.",
    )
    # - Attributes ----------
    order: int = Field(
        description="Order of the stationary point (minimum = 0, transition = 1, ...)"
    )
    is_pseudo: bool = Field(description="Whether this is a pseudo stationary point.")
    # - Linked table --------
    geometry: "GeometryRow" = Relationship(back_populates="stationary_point")
    calculation: "CalculationRow" = Relationship(back_populates="stationary_points")
    # - Linked tables -------
    identities: list["IdentityRow"] = Relationship(
        back_populates="stationary_points", link_model=StationaryIdentityLink
    )
    metrics: list["MetricRow"] = Relationship(
        back_populates="stationary_point",
    )
    stages: list["StageRow"] = Relationship(
        back_populates="stationary_points", link_model=StationaryStageLink
    )


class IdentityRow(SQLModel, table=True):
    """Stationary point identities."""

    # - SQL Metadata --------
    __tablename__ = "identity"
    # - Row id --------------
    id: RowID | None = Field(default=None, primary_key=True)
    # - Foreign keys --------
    # - Attributes ----------
    type: str = Field(description="Category of the identity (stereoisomer, ...)")
    algorithm: str = Field(description="Method used to determine identity (InChI, ...)")
    value: str = Field(description="Value of the identity algorithm.")
    # - Linked table --------
    # - Linked tables -------
    stationary_points: list["StationaryPointRow"] = Relationship(
        back_populates="identities", link_model=StationaryIdentityLink
    )


class MetricRow(SQLModel, table=True):
    """Metrics for comparing conformers."""

    # - SQL Metadata --------
    __tablename__ = "metric"
    # - Row id --------------
    id: RowID | None = Field(default=None, primary_key=True)
    # - Foreign keys --------
    stationary_id: RowID = Field(
        foreign_key="stationary_point.id",
        index=True,
        description="Foreign key to the linked stationary point.",
    )
    # - Attributes ----------
    type: str = Field(description="Category of the metric (Inertia Tensor, ...)")
    algorithm: str = Field(description="Method used to determine metric (Kabsch, ...)")
    value: str = Field(description="Value of the metric algorithm.")
    # - Linked table --------
    stationary_point: "StationaryPointRow" = Relationship(back_populates="metrics")
    # - Linked tables -------


# --- Stage Models ------------------------------
class StageRow(SQLModel, table=True):
    """Reaction stage."""

    # - SQL Metadata --------
    __tablename__ = "stage"
    # - Row id --------------
    id: RowID | None = Field(default=None, primary_key=True)
    # - Foreign keys --------
    # - Attributes ----------
    is_ts: bool = Field(description="Stage represents transition state.")
    # - Linked table --------
    steps_1: list["StepRow"] = Relationship(
        back_populates="stage1",
        sa_relationship_kwargs={"foreign_keys": "[StepRow.stage_id1]"},
    )
    steps_2: list["StepRow"] = Relationship(
        back_populates="stage2",
        sa_relationship_kwargs={"foreign_keys": "[StepRow.stage_id2]"},
    )
    steps_ts: list["StepRow"] = Relationship(
        back_populates="stage_ts",
        sa_relationship_kwargs={"foreign_keys": "[StepRow.stage_id_ts]"},
    )
    # - Linked tables -------
    stationary_points: list["StationaryPointRow"] = Relationship(
        back_populates="stages", link_model=StationaryStageLink
    )


# --- Stage Models ------------------------------
class StepRow(SQLModel, table=True):
    """Reaction step."""

    # - SQL Metadata --------
    __tablename__ = "step"
    # - Row id --------------
    id: RowID | None = Field(default=None, primary_key=True)
    # - Foreign keys --------
    stage_id1: RowID = Field(
        foreign_key="stage.id",
        index=True,
        description="Foreign key to the 1st reaction stage.",
    )
    stage_id2: RowID = Field(
        foreign_key="stage.id",
        index=True,
        description="Foreign key to the 2nd reaction stage.",
    )
    stage_id_ts: RowID = Field(
        foreign_key="stage.id",
        index=True,
        description="Foreign key to the TS reaction stage.",
    )
    # - Attributes ----------
    is_barrierless: bool = Field(
        description="Reaction step does not involve a TS stage."
    )
    # - Linked table --------
    stage1: "StageRow" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[StepRow.stage_id1]"}
    )
    stage2: "StageRow" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[StepRow.stage_id2]"}
    )
    stage_ts: "StageRow" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[StepRow.stage_id_ts]"}
    )
    # - Linked tables -------


# --- Listeners ---------------------------------
@event.listens_for(GeometryRow, "before_insert")
def populate_geometry_hash(mapper, connection, target: GeometryRow) -> None:  # noqa: ANN001, ARG001
    """Populate GeometryRow hash before inserts and updates."""
    if target.hash is None:
        target.hash = geom.geometry_hash(target)


@event.listens_for(Session, "after_flush")
def populate_calculation_hashes(session, flush_context) -> None:  # noqa: ANN001, ARG001
    """Populate the 'minimal' hash for newly added CalculationRow objects."""
    available = set(hash_registry.available())

    for row in session.new:
        if not isinstance(row, CalculationRow):
            continue

        existing = {h.name for h in row.hashes}
        missing = available - existing
        if not missing:
            continue

        calc = row

        for name in missing:
            value = calculation_hash(calc, name=name)

            session.add(
                CalculationHashRow(
                    calculation_id=row.id,
                    name=name,
                    value=value,
                )
            )


@event.listens_for(StationaryPointRow, "after_insert")
def stationary_inchi(mapper, connection, target: StationaryPointRow) -> None:  # noqa: ANN001, ARG001
    """Automatically tags InChI and default metrics after inserting StationaryPoint."""
    session = Session(bind=connection)

    if target.id is None:
        msg = f"{target = } not assigned an id."
        raise LookupError(msg)

    try:
        # NOTE: If target.geometry isn't loaded, we need to fetch it
        geom_stmt = select(GeometryRow).where(GeometryRow.id == target.geometry_id)
        geom_row = session.exec(geom_stmt).first()

        if not geom_row:
            msg = (
                f"{target.geometry_id} does not correspond to an entry in the database."
            )
            raise LookupError(msg)  # noqa: TRY301

        inchi_string = geom.inchi(geom_row)

        inchi_stmt = select(IdentityRow).where(
            IdentityRow.algorithm == "InChI", IdentityRow.value == inchi_string
        )
        id_row = session.exec(inchi_stmt).first()

        if id_row is None:
            id_row = IdentityRow(
                type="stereoisomer",
                algorithm="InChI",
                value=inchi_string,
            )
            session.add(id_row)
            session.flush()

        if id_row.id is None:
            msg = f"{id_row = } not assigned an id."
            raise LookupError(msg)  # noqa: TRY301

        link = StationaryIdentityLink(stationary_id=target.id, identity_id=id_row.id)
        session.add(link)

        session.commit()

    except Exception as e:
        session.rollback()
        msg = f"Failed to generate InChI {target.id}"
        raise RuntimeError(msg) from e
