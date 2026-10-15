from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.session import SessionLocal
from app.crud import consents as crud
from app.schemas.consent import ConsentCreate, ConsentResponse, ConsentListResponse, ConsentData, WithdrawRequest, PermissionCreate, PolicyCreate
from app.auth.dependencies import require_token
from fastapi import Depends
from fastapi.responses import JSONResponse
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

from app.keycloak_instance import kc

# logger = logging.getLogger(__name__)


router = APIRouter(prefix="/consents", tags=["consents"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Get all registered consents
@router.get("", response_model=ConsentListResponse)
def get_all_consents(db: Session = Depends(get_db), token=Depends(require_token("admin"))):
    try:
        consents = crud.get_all_consents(db)
        consent_data_list = [ConsentData.model_validate(c) for c in consents]
        return ConsentListResponse(data=consent_data_list, success=True)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Unexpected error occurred", "detail": str(e)}
        )


# get consent with consent_id
@router.get("/{consent_id}", response_model=ConsentResponse)
def get_consent_by_id(consent_id: UUID, db: Session = Depends(get_db), token=Depends(require_token("admin"))):
    try:
        consent_data = crud.get_consent(db, consent_id)
        return ConsentResponse(data=consent_data, success=True)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Unexpected error occurred", "detail": str(e)}
        )


# create new consent
@router.post("", response_model=ConsentResponse)
async def give_consent(consent: ConsentCreate, db: Session = Depends(get_db), token=Depends(require_token("admin"))):
    try:
        consent_data = crud.create_consent(db, consent)

        ###
        # update permissions and policies
        # get user info
        # user_info = await kc.get_user_by_id(user_id=consent.given_to)

        # logger.debug(f"user info: {user_info}")

        # # create policy allowing the user access the resource
        # policy_response = await kc.create_user_based_policy(
        #     client_uuid=consent.client_id, 
        #     user=consent.given_to, 
        #     name=f"allow_{user_info.get('data').get('username')}", 
        #     description="", 
        #     logic="POSITIVE", 
        #     decision_strategy="UNANIMOUS"
        #     )
        
        # # write policy to db and update reference to consent
        # cpol = PolicyCreate(id=policy_response.get("data").get("id"))
        # policy = crud.create_policy(db, consent_data, cpol)
        
        # create permission allowing the user accessing the resource for the set scope
        # permission_response = await kc.create_scope_based_permission(
        #     client_uuid=consent.client_id, 
        #     name=f"{user_info.get('data').get('username')}_can_{consent.scope}", 
        #     description='', 
        #     resources=[consent.resource_id], 
        #     scopes=[consent.scope], 
        #     policies=[policy_response.get('data').get('name')]
        #     )
        
        # write permission to db and update reference to consent
        # cper = PermissionCreate(id=permission_response.get("data").get("id"))
        # permission = crud.create_permission(db, consent_data, cper)

        return ConsentResponse(data=consent_data, success=True) 
    
    except IntegrityError as e:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Consent already exists or violates constraints."}
        )
    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Unexpected error occurred", "detail": str(e)}
        )


# withdraw consent
@router.put("/{consent_id}", response_model=ConsentResponse)
async def withdraw(consent_id: str, request: WithdrawRequest, db: Session = Depends(get_db), token=Depends(require_token("admin"))):
    try:
        consent_data = crud.get_consent(db, consent_id)
        
        # # remove permissions from keycloak
        # permissions = crud.get_permissions(db, consent_id)
        # for permission in permissions:
        #     await kc.delete_permission(client_uuid=consent_data.client_id, permission_id=permission.get("id"))

        # # remove policies from keycloak
        # policies = crud.get_policies(db, consent_id)
        # for policy in policies:
        #     await kc.delete_policy(client_uuid=consent_data.client_id, policy_id=policy.get("id"))
        
        crud.withdraw_consent(db, consent_id, request.reason)

        return ConsentResponse(data=consent_data, success=True) 
    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Unexpected error occurred", "detail": str(e)}
        )
    










