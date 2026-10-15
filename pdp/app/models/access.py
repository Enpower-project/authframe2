from __future__ import annotations
import uuid
from typing import Optional
from sqlalchemy import (
    text, 
    String,
    ForeignKey, 
    Text, 
    CheckConstraint, 
    TIMESTAMP, 
    Index,
    UniqueConstraint,
    PrimaryKeyConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.base import Base
from datetime import datetime



class Tenant(Base):
    __tablename__ = "tenants"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")) # requires pgcrypto extension
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'active'"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"), server_onupdate=text("now()"))

    __table_args__ = (
        CheckConstraint("status IN ('active','suspended','deleted')", name="ck_tenants_status_valid"),
    )
    records: Mapped[list[Record]] = relationship(back_populates="tenant", cascade="all, delete-orphan") 
    resources: Mapped[list["Resource"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    role_bindings: Mapped[list["TenantRoleBinding"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    users: Mapped[list["SubjectMap"]] = relationship(secondary="tenant_role_binding", viewonly=True)
    


class SubjectMap(Base):
    __tablename__ = "subject_map"

    principal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    idp_ref: Mapped[str] = mapped_column(Text, nullable=False)     # ID of subject by identity provider    
    idp_issuer: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (
        UniqueConstraint("idp_ref", "idp_issuer", name="uq_subject_map_identity"),
    )
    tenant_roles: Mapped[list["TenantRoleBinding"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class RoleBinding(Base):
    __tablename__ = "role_binding"

    principal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)             # reader|writer|admin...
    scope_type: Mapped[str] = mapped_column(Text, nullable=False)       # tenant|project|dataset...
    scope_id: Mapped[str] = mapped_column(Text, nullable=False)
    valid_from: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    valid_to: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))

    __table_args__ = (
        PrimaryKeyConstraint("principal_id", "role", "scope_type", "scope_id", name="pk_role_binding"),
    )


class TenantRoleBinding(Base):
    __tablename__ = "tenant_role_binding"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id", ondelete="CASCADE"), nullable=False)
    principal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subject_map.principal_id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)             # reader|writer|admin...
    valid_from: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    valid_to: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))

    __table_args__ = (
        PrimaryKeyConstraint("tenant_id", "principal_id", "role", name="pk_tenant_role_binding"),
    )
    tenant: Mapped["Tenant"] = relationship(back_populates="role_bindings")
    user: Mapped["SubjectMap"] = relationship(back_populates="tenant_roles")


class Resource(Base):
    __tablename__ = "resources"

    resource_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id", ondelete="CASCADE"),nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subject_map.principal_id", ondelete="SET NULL"), nullable=True,)
    type: Mapped[str] = mapped_column(Text, nullable=False)          # e.g., "record", "dataset", "project"
    name: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True),nullable=False,server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True),nullable=False,server_default=text("now()"),server_onupdate=text("now()"))

    tenant: Mapped["Tenant"] = relationship(back_populates="resources")
    owner: Mapped[Optional["SubjectMap"]] = relationship()

    __table_args__ = (
        Index("idx_resources_tenant_id", "tenant_id"),
        Index("idx_resources_type", "type"),
        UniqueConstraint("tenant_id", "type", "name", name="uq_resource_name_per_tenant"),
        UniqueConstraint("tenant_id", "url", name="uq_resource_url_per_tenant"),
    )

# tuple-based access control — an authorization model where each permission is a 4-part tuple:
class TupleACL(Base):
    __tablename__ = "tuple_acl"

    object_ns: Mapped[str] = mapped_column(Text, nullable=False)        # object namespace, e.g., record, dataset, project, etc.)
    object_id: Mapped[str] = mapped_column(Text, nullable=False)
    relation: Mapped[str] = mapped_column(Text, nullable=False)         # viewer|editor|owner
    subject: Mapped[str] = mapped_column(Text, nullable=False)          # "user:<principal_id>" or "group:<group_id>"

    __table_args__ = (
        PrimaryKeyConstraint("object_ns", "object_id", "relation", "subject", name="pk_tuple_acl"), 
        Index("idx_tuple_acl_object", "object_ns", "object_id"),
    )


class Record(Base):
    __tablename__ = "records"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),  ForeignKey("tenants.tenant_id", ondelete="CASCADE"), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    tenant: Mapped[Tenant] = relationship(back_populates="records")  

    __table_args__ = (
        Index("idx_records_tenant_id", "tenant_id"),
    )


# class Member(Base):
#     __tablename__ = "members"

#     member_id = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
#     external_ref = Column(UUID(as_uuid=True), unique=True)
#     name = Column(Text, nullable=False)
#     first_name = Column(Text, nullable=False)
#     last_name = Column(Text, nullable=False)
#     email = Column(Text, nullable=False)
#     type = Column(Text, CheckConstraint("type IN ('prosumer','consumer','producer')"))
#     created_at = Column(DateTime(timezone=True), server_default="now()")
#     service_points = relationship("ServicePoint", back_populates="member")


# class GridElement(Base):
#     __tablename__ = "grid_elements"

#     grid_element_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     parent_id = Column(UUID(as_uuid=True), ForeignKey("grid_elements.grid_element_id"), nullable=True)
#     code = Column(Text, unique=True, nullable=False)
#     type = Column(
#         Enum("TSO","HV_SUB","MV_FEEDER","LV_SUB","TRANSFORMER","SWITCH","NODE",
#              name="grid_element_type"),
#         nullable=False
#     )
#     name = Column(Text)
#     voltage_level = Column(Text)   # e.g. "0.4kV", "20kV"
#     location = Column(Text)        # if not using PostGIS, store as WKT or JSON
#     created_at = Column(TIMESTAMP, server_default="now()")
#     parent = relationship("GridElement", remote_side=[grid_element_id], backref="children")
#     service_points = relationship("ServicePoint", back_populates="grid_element")


# class ServicePoint(Base):
#     __tablename__ = "service_points"

#     sp_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     member_id = Column(UUID(as_uuid=True), ForeignKey("members.member_id"), nullable=False)
#     code = Column(Text, unique=True, nullable=False)
#     voltage_level = Column(Text)
#     address = Column(JSON)
#     timezone = Column(Text, nullable=False)
#     active = Column(Boolean, default=True)
#     # link the service point to the member id
#     member = relationship("Member", back_populates="service_points")
#     # link the service point to the grid element (substation, transformer, etc.)
#     grid_element_id = Column(UUID(as_uuid=True), ForeignKey("grid_elements.grid_element_id"))
#     grid_element = relationship(GridElement, back_populates="service_points")
#     meters = relationship("Meter", back_populates="service_point")


# class Meter(Base):
#     __tablename__ = "meters"

#     meter_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     sp_id = Column(UUID(as_uuid=True), ForeignKey("service_points.sp_id"), nullable=False)
#     serial_no = Column(Text, nullable=False)
#     model = Column(Text)
#     installed_at = Column(DateTime(timezone=True))
#     service_point = relationship("ServicePoint", back_populates="meters")
#     channels = relationship("Channel", back_populates="meter")


# class Channel(Base):
#     __tablename__ = "channels"

#     channel_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     meter_id = Column(UUID(as_uuid=True), ForeignKey("meters.meter_id"), nullable=False)
#     role = Column(
#         Enum("import", "export", "reactive_import", "reactive_export", "voltage", "current", name="meter_role"), 
#         nullable=False
#     )
#     uom = Column(
#         Enum("kWh", "kW", "kvarh", "kvar", "Wh", "W", "V", "A", name="unit_of_measure"), 
#         nullable=False
#     )
#     interval_minutes = Column(Integer, CheckConstraint("interval_minutes IN (1,5,10,15,30,60)"), nullable=False)
#     scaling_factor = Column(Numeric, default=1.0)
#     meter = relationship("Meter", back_populates="channels")
#     readings = relationship("Reading", back_populates="channel")


# -- 1) Tenants (canonical)
# CREATE TABLE tenants (
#   tenant_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
#   slug        TEXT UNIQUE NOT NULL,          -- e.g., 'ec_jug'
#   name        TEXT NOT NULL,
#   status      TEXT NOT NULL DEFAULT 'active',-- active|suspended|deleted
#   created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
#   updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
# );

# -- 1) One-way-ish index for lookups (store as little as possible)
# CREATE TABLE subject_map (
#   principal_id   UUID PRIMARY KEY,           -- your app's opaque ID
#   kc_sub         TEXT NOT NULL,              -- Keycloak subject (UUID)
#   idp_issuer     TEXT NOT NULL,              -- e.g., https://keycloak.local/realms/ENPOWER
#   tenant_id      TEXT NOT NULL,
#   created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
#   UNIQUE (kc_sub, idp_issuer, tenant_id)
# );

# -- 2) Role bindings (RBAC) at a scope (realm/tenant/project)
# CREATE TABLE role_binding (
#   principal_id   UUID NOT NULL,
#   role           TEXT NOT NULL,              -- reader|writer|admin...
#   scope_type     TEXT NOT NULL,              -- tenant|project|dataset...
#   scope_id       TEXT NOT NULL,
#   valid_from     TIMESTAMPTZ,
#   valid_to       TIMESTAMPTZ,
#   PRIMARY KEY (principal_id, role, scope_type, scope_id)
# );

# -- 3) Tenant role bindings (tenant-scoped RBAC)
# CREATE TABLE tenant_role_binding (
#   tenant_id    UUID NOT NULL REFERENCES tenants(tenant_id),
#   principal_id UUID NOT NULL,
#   role         TEXT NOT NULL,                -- reader|writer|admin...
#   valid_from   TIMESTAMPTZ,
#   valid_to     TIMESTAMPTZ,
#   PRIMARY KEY (tenant_id, principal_id, role)
# );

# -- 3) Optional ReBAC (object sharing)
# CREATE TABLE tuple_acl (
#   object_ns      TEXT NOT NULL,              -- e.g., "record"
#   object_id      TEXT NOT NULL,
#   relation       TEXT NOT NULL,              -- viewer|editor|owner
#   subject        TEXT NOT NULL,              -- "user:<principal_id>" or "group:<group_id>"
#   PRIMARY KEY (object_ns, object_id, relation, subject)
# );


# -- 4) Example business table with strict tenancy
# CREATE TABLE records (
#   id         TEXT PRIMARY KEY,
#   tenant_id  UUID NOT NULL REFERENCES tenants(tenant_id),
#   payload    JSONB NOT NULL
# );
# CREATE INDEX ON records (tenant_id);