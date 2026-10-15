from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timezone
from app.models import access
from fastapi import HTTPException
# from app.schemas.user import UserCreateDB, UserData
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


def get_all_users(db: Session):
    return db.query(access.SubjectMap).all()


def get_user_principal_id(db: Session, user_idp_id: UUID):
    db_user = db.query(access.SubjectMap).filter(
        access.SubjectMap.idp_ref == user_idp_id
    ).one_or_none()

    principal_id = None

    try:
        principal_id = db_user.principal_id
    except Exception as e:
        logger.exception(f"e")

    return principal_id


# def get_all_consents(db: Session):
#     return db.query(mdms.Consent).all()


# def get_consent(db: Session, consent_id: UUID):
#     consent = db.query(mdms.Consent).filter(
#         mdms.Consent.id == consent_id
#     ).one_or_none()

#     if consent is None:
#         raise HTTPException(status_code=404, detail="Consent not found")
    
#     return ConsentData.model_validate(consent)


# def get_user_consents(db: Session, user_id: str):
#     return db.query(mdms.Consent).filter(
#         or_(
#             mdms.Consent.given_by == user_id,
#             mdms.Consent.given_to == user_id
#         )
#     ).all()


# def create_consent(db: Session, consent: ConsentCreate):
#     db_consent = mdms.Consent(**consent.model_dump())
#     db.add(db_consent)
#     db.commit()
#     db.refresh(db_consent)
#     return ConsentData.model_validate(db_consent)


# def create_permission(db:Session, consent: ConsentData, permission: PermissionCreate):
#     db_permission = mdms.Permission(**permission.model_dump())
#     db_consent = db.query(mdms.Consent).filter(
#         mdms.Consent.id == consent.consent_id
#     ).one_or_none()
#     db.add(db_permission)
#     db_consent.permissions.append(db_permission)
#     db.commit()
#     db.refresh(db_permission)
#     return PermissionData.model_validate(db_permission)


# def get_permissions(db:Session, consent_id: UUID):
#     db_consent = db.query(mdms.Consent).filter(
#         mdms.Consent.id == consent_id
#     ).one_or_none()
#     permissions = db_consent.permissions

#     perlist = []
#     for perm in permissions:
#         perlist.append({'id': perm.id, 'granted_at': perm.granted_at})

#     return perlist


# def get_policies(db:Session, consent_id: UUID):
#     db_consent = db.query(mdms.Consent).filter(
#         mdms.Consent.id == consent_id
#     ).one_or_none()
#     policies = db_consent.policies

#     polist = []
#     for pol in policies:
#         polist.append({'id': pol.id, 'granted_at': pol.granted_at})

#     return polist


# def create_policy(db:Session, consent: ConsentData, policy: PolicyCreate):
#     db_policy = mdms.Policy(**policy.model_dump())
#     db_consent = db.query(mdms.Consent).filter(
#         mdms.Consent.id == consent.consent_id
#     ).one_or_none()
#     db.add(db_policy)
#     db_consent.policies.append(db_policy)
#     db.commit()
#     db.refresh(db_policy)
#     return PolicyData.model_validate(db_policy)
    

# def withdraw_consent(db: Session, consent_id: str, reason: str):
#     consent = db.query(mdms.Consent).get(consent_id)

#     # remove permissions
#     for permission in list(consent.permissions):  
#         consent.permissions.remove(permission)   
#         db.delete(permission)    

#     # remove policies
#     for policy in list(consent.policies):
#         consent.policies.remove(policy)
#         db.delete(policy)

#     consent.consent_status = 'withdrawn'
#     consent.reason = reason
#     consent.validity_until = None
#     consent.timestamp_updated = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
#     db.commit()
#     db.refresh(consent)

#     return ConsentData.model_validate(consent)


# def get_all_consent_requests(db: Session):
#     return db.query(mdms.ConsentRequest).all()


# def get_consent_request(db: Session, request_id: UUID):
#     consent_request = db.query(mdms.ConsentRequest).filter(
#         mdms.ConsentRequest.id == request_id
#     ).one_or_none()

#     if consent_request is None:
#         raise HTTPException(status_code=404, detail="Consent request not found")
    
#     return ConsentRequestData.model_validate(consent_request)


# def create_consent_request(db: Session, request: ConsentRequestCreate):
#     db_consent_request = mdms.ConsentRequest(**request.model_dump())
#     db.add(db_consent_request)
#     db.commit()
#     db.refresh(db_consent_request)
#     return ConsentRequestData.model_validate(db_consent_request)


# def reject_consent_request(db: Session, request_id: UUID):
#     consent_request = db.query(mdms.ConsentRequest).filter(
#         mdms.ConsentRequest.id == request_id
#     ).one_or_none()

#     if consent_request is None:
#         raise HTTPException(status_code=404, detail="Consent request not found")
    
#     consent_request.request_status = 'rejected'
#     consent_request.updated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
#     db.commit()
#     db.refresh(consent_request)
    
#     return ConsentRequestData.model_validate(consent_request)


# def approve_consent_request(db: Session, request_id: UUID):
#     consent_request = db.query(mdms.ConsentRequest).filter(
#         mdms.ConsentRequest.id == request_id
#     ).one_or_none()

#     if consent_request is None:
#         raise HTTPException(status_code=404, detail="Consent request not found")
    
#     consent_request.request_status = 'approved'
#     consent_request.updated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
#     db.commit()
#     db.refresh(consent_request)
    
#     return ConsentRequestData.model_validate(consent_request)

