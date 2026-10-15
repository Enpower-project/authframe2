from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.session import SessionLocal
import app.crud.tenants as tenants
from app.schemas.tenant import TenantCreate, TenantResponse, TenantListResponse, TenantData
from app.auth.dependencies import require_token
from fastapi import Depends
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

from app.keycloak_instance import kc


router = APIRouter(prefix="/tenants", tags=["tenants"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@router.get("", response_model=TenantListResponse)
async def get_all_tenants(db: Session = Depends(get_db), token=Depends(require_token("admin"))):
    try:
        response = tenants.get_all_tenants(db)
        tenant_data_list = [TenantData.model_validate(t) for t in response]
        return TenantListResponse(data=tenant_data_list, success=True)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Unexpected error occurred", "detail": str(e)}
        )


@router.post("", response_model=TenantResponse)
async def create_tenant(tenant: TenantCreate, db: Session = Depends(get_db), token=Depends(require_token("admin"))):
    try:
        logger.debug("Start creating tenant")
        tenant_data = tenants.create_tenant(db, tenant)
        logger.debug(f"response: {tenant_data}")

        ###
        # add tenant also to Keycloak

        # create base tenant group
        # response = await kc.create_group(group_name=tenant.slug)
        # logger.debug(f"user create response: {response}")

        # # get group/tenant id
        # groups = await kc.get_all_groups()
        # logger.debug(f"tenants: {groups}")
        # group_id = None
        # for group in groups["data"]:
        #     if tenant.slug == group.get("name"):
        #         group_id = group.get("id")
        # logger.debug(f"group_id: {group_id}")
        # create subgroups

        return TenantResponse(data=tenant_data, success=True) 
    
    except IntegrityError as e:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Tenant already exists or violates constraints."}
        )
    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Unexpected error occurred", "detail": str(e)}
        )

