import uuid
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


consent_policies = Table(
    "consent_policies",
    Base.metadata,
    Column("consent_id", UUID(as_uuid=True), ForeignKey("consents.id"), primary_key=True),
    Column("policy_id", UUID(as_uuid=True), ForeignKey("policies.id"), primary_key=True)
)


consent_permissions = Table(
    "consent_permissions",
    Base.metadata,
    Column("consent_id", UUID(as_uuid=True), ForeignKey("consents.id"), primary_key=True),
    Column("permission_id", UUID(as_uuid=True), ForeignKey("permissions.id"), primary_key=True)
)


class Consent(Base):
    __tablename__ = "consents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    resource_id = Column(UUID(as_uuid=True), index=True)
    scope = Column(String)
    purpose = Column(String)
    given_by = Column(UUID(as_uuid=True), index=True)
    given_to = Column(UUID(as_uuid=True), index=True)
    client_id = Column(UUID(as_uuid=True), index=True)
    consent_status = Column(String, default='inactive')
    reason = Column(String, nullable=True, default=None)
    policies = relationship("Policy", secondary="consent_policies", back_populates="consents", cascade="all, delete")
    permissions = relationship("Permission", secondary="consent_permissions", back_populates="consents", cascade="all, delete")
    validity_until = Column(DateTime(timezone=True), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    timestamp_updated = Column(DateTime(timezone=True), server_default=func.now())


class ConsentRequest(Base):
    __tablename__ = "consent_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    resource_id = Column(UUID(as_uuid=True), index=True)
    scope = Column(String)
    purpose = Column(String)
    owner_id = Column(UUID(as_uuid=True), index=True)
    requesting_party_id = Column(UUID(as_uuid=True), index=True)
    client_id = Column(UUID(as_uuid=True), index=True)
    request_status = Column(String, default='pending')  # options: pending, approved, rejected
    validity_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    consents = relationship("Consent", secondary="consent_permissions", back_populates="permissions")
    

class Policy(Base):
    __tablename__ = "policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    consents = relationship("Consent", secondary="consent_policies", back_populates="policies")


# class ConsentPermissionRelation(Base):
#     __tablename__ = "consent_permissions"

#     consent_id = Column(UUID(as_uuid=True), ForeignKey("consents.id"), primary_key=True)
#     permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id"), primary_key=True)
#     consent = relationship("Consent", back_populates="consent_permissions")
#     permission = relationship("Permission", back_populates="consent_permissions")


# class ConsentPolicyRelation(Base):
#     __tablename__ = "consent_policies"

#     consent_id = Column(UUID(as_uuid=True), ForeignKey("consents.id"), primary_key=True)
#     policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id"), primary_key=True)
#     consent = relationship("Consent", back_populates="consent_policies")
#     policy = relationship("Policy", back_populates="consent_policies")


    