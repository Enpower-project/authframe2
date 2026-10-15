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


