from fastapi import APIRouter, Depends
from app.auth.dependencies import require_token
from fastapi import Depends, status
from fastapi.responses import JSONResponse
from app.schemas.client import ClientCreateRequest, ClientUpdateRequest
import logging

from app.keycloak_instance import kc

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/clients", tags=["clients"])

@router.get("")
async def get_clients(token=Depends(require_token("admin"))):

    response = await kc.get_realm_clients()

    logger.info(f"client: {response}")

    if response.get("success"):
        return JSONResponse(
            content=response,
            status_code=status.HTTP_200_OK
        )
    else:
        return JSONResponse(
            content=response,
            status_code=response.get("status", status.HTTP_400_BAD_REQUEST)
        )


@router.post("")
async def create_client(request: ClientCreateRequest, token=Depends(require_token("admin"))):
    logger.info(f"request_data: {request}")

    response = await kc.create_client(
        client_id=request.client_id, 
        client_name=request.client_id,
        protocol="openid-connect", 
        public_client=False, 
        redirect_uris=request.redirect_uris, 
        base_url=request.base_url, 
        admin_url=request.admin_url, 
        standard_flow_enabled=True,
        secret=request.secret, 
        service_accounts_enabled=True,
        direct_access_grants_enabled=True, 
        authorization_services_enabled=True,
        always_display_in_console=True,
        enabled=request.enabled)

    logger.info(f"client: {response}")

    if response.get("success"):
        return JSONResponse(
            content=response,
            status_code=status.HTTP_201_CREATED
        )
    else:
        return JSONResponse(
            content=response,
            status_code=response.get("status", status.HTTP_400_BAD_REQUEST)
        )
    

@router.get("/{client_id}")
async def get_client(client_id, token=Depends(require_token("admin"))):
    response = await kc.get_client_by_id(client_id=client_id)

    logger.info(f"client: {response}")

    if response.get("success"):
        return JSONResponse(
            content=response,
            status_code=status.HTTP_200_OK
        )
    else:
        return JSONResponse(
            content=response,
            status_code=response.get("status", status.HTTP_400_BAD_REQUEST)
        )
    

@router.put("/{client_id}")
async def update_client(client_id, request: ClientUpdateRequest, token=Depends(require_token("admin"))):
    response = await kc.update_client(
        client_uuid=client_id,
        client_name=request.client_name,
        protocol="openid-connect", 
        public_client=False, 
        redirect_uris=request.redirect_uris, 
        base_url=request.base_url, 
        admin_url=request.admin_url, 
        standard_flow_enabled=True,
        secret=request.secret, 
        service_accounts_enabled=True,
        direct_access_grants_enabled=True, 
        authorization_services_enabled=True,
        always_display_in_console=True,
        enabled=request.enabled)
    
    logger.info(f"response: {response}")

    if response.get("success"):
        return JSONResponse(
            content={
                "message": "Client updated"
            },
            status_code=status.HTTP_200_OK
        )
    else:
        return JSONResponse(
            content={
                "error": "Failed to update client",
                "details": response.get("error")
            },
            status_code=response.get("status", status.HTTP_400_BAD_REQUEST)
        )


@router.delete("/{client_id}")
async def delete_client(client_id, token=Depends(require_token("admin"))):
    response = await kc.delete_client(client_id=client_id)
    
    logger.info(f"response: {response}")

    if response.get("success"):
        return JSONResponse(
            content={
                "message": "Client deleted"
            },
            status_code=status.HTTP_200_OK
        )
    else:
        return JSONResponse(
            content={
                "error": "Failed to delete client",
                "details": response.get("error")
            },
            status_code=response.get("status", status.HTTP_400_BAD_REQUEST)
        )