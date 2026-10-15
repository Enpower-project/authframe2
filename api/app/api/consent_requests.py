from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.session import SessionLocal
from app.crud import consents as crud
from app.schemas.consent import PolicyCreate, PermissionCreate, ConsentRequestData, ConsentRequestCreate, ConsentRequestResponse, ConsentRequestListResponse, ConsentResponse, ConsentCreate
from app.auth.dependencies import require_token
from fastapi import Depends
from fastapi.responses import JSONResponse
from uuid import UUID
import logging

from app.keycloak_instance import kc

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/consent-requests", tags=["consent-requests"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=ConsentRequestListResponse)
def get_consent_requests(db: Session = Depends(get_db), token=Depends(require_token("admin"))):
    try:
        consent_requests = crud.get_all_consent_requests(db)
        consent_req_data_list = [ConsentRequestData.model_validate(c) for c in consent_requests]
        return ConsentRequestListResponse(data=consent_req_data_list, success=True)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Unexpected error occurred", "detail": str(e)}
        )


@router.get("/{request_id}", response_model=ConsentRequestResponse)
def get_consent_request(request_id: UUID, db: Session = Depends(get_db), token=Depends(require_token("admin"))):
    try:
        consent_request = crud.get_consent_request(db, request_id)
        return ConsentRequestResponse(data=consent_request, success=True)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Unexpected error occurred", "detail": str(e)}
        )


@router.post("", response_model=ConsentRequestResponse)
def create_new_consent_request(request: ConsentRequestCreate, db: Session = Depends(get_db), token=Depends(require_token("admin"))):
    try:
        consent_request_data = crud.create_consent_request(db, request)
        return ConsentRequestResponse(data=consent_request_data, success=True) 
    except IntegrityError as e:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Consent request already exists or violates constraints."}
        )
    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Unexpected error occurred", "detail": str(e)}
        )


@router.post("/{request_id}/approve", response_model=ConsentResponse)
async def approve_consent_request(request_id: UUID, db: Session = Depends(get_db), token=Depends(require_token("admin"))):
    try:
        # get consent request by ID
        consent_request = crud.get_consent_request(db, request_id)
        # prepare consent create request object
        request = ConsentCreate(
            resource_id=str(consent_request.resource_id),
            scope=consent_request.scope,
            purpose=consent_request.purpose,
            given_by=str(consent_request.owner_id),
            given_to=str(consent_request.requesting_party_id),
            client_id=str(consent_request.client_id),
            consent_status='active',
            validity_until=str(consent_request.validity_until)
            )
        # create new consent
        consent_data = crud.create_consent(db, request)

        ###
        # update permissions and policies
        # get user info
        user_info = await kc.get_user_by_id(user_id=consent_data.given_to)

        logger.debug(f"user info: {user_info}")

        # create policy allowing the user access the resource
        policy_response = await kc.create_user_based_policy(
            client_uuid=consent_data.client_id, 
            user=consent_data.given_to, 
            name=f"allow_{user_info.get('data').get('username')}", 
            description="", 
            logic="POSITIVE", 
            decision_strategy="UNANIMOUS"
            )
        
        # write policy to db and update reference to consent
        cpol = PolicyCreate(id=policy_response.get("data").get("id"))
        policy = crud.create_policy(db, consent_data, cpol)
        
        # create permission allowing the user accessing the resource for the set scope
        permission_response = await kc.create_scope_based_permission(
            client_uuid=consent_data.client_id, 
            name=f"{user_info.get('data').get('username')}_can_{consent_data.scope}", 
            description='', 
            resources=[consent_data.resource_id], 
            scopes=[consent_data.scope], 
            policies=[policy_response.get('data').get('name')]
            )
        
        # write permission to db and update reference to consent
        cper = PermissionCreate(id=permission_response.get("data").get("id"))
        permission = crud.create_permission(db, consent_data, cper)

        # update consent request object
        crud.approve_consent_request(db, request_id)
        
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


@router.post("/{request_id}/reject", response_model=ConsentRequestResponse)
def deny_consent_request(request_id: UUID, db: Session = Depends(get_db), token=Depends(require_token("admin"))):
    try:
        # reject consent request
        consent_request = crud.reject_consent_request(db, request_id)
        return ConsentRequestResponse(data=consent_request, success=True) 
    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Unexpected error occurred", "detail": str(e)}
        )



