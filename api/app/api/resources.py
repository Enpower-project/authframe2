from fastapi import APIRouter, Depends, HTTPException
from app.auth.dependencies import require_token
from fastapi import Depends, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.session import SessionLocal
from app.crud import resources 
from enum import Enum
from uuid import UUID
from app.schemas.resource import ResourceCreateRequest, ResourceResponse, ResourceListResponse, ResourceData
from app.schemas.consent import ConsentData, ConsentListResponse
import logging
from authzed.api.v1 import (
    ObjectReference,
    Relationship,
    RelationshipUpdate,
    SubjectReference,
    WriteRelationshipsRequest,
    InsecureClient,
    ReadRelationshipsRequest,
    RelationshipFilter
)

from app.keycloak_instance import kc

logger = logging.getLogger(__name__)

SPICEDB_TOKEN = "supersecretkey"
# client = Client("spicedb:50051", bearer_token_credentials(SPICEDB_TOKEN))
client = InsecureClient("spicedb:50051", SPICEDB_TOKEN)


router = APIRouter(prefix="/resources", tags=["resources"])

class PermissionScope(str, Enum):
    read = "read"
    edit = "edit"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=ResourceListResponse)
async def get_resources(db: Session = Depends(get_db), token=Depends(require_token("admin"))):
    try:
        response = resources.get_all_resources(db)
        resources_data_list = [ResourceData.model_validate(r) for r in response]
        return ResourceListResponse(data=resources_data_list, success=True)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Unexpected error occurred", "detail": str(e)}
        )


# create resource for specific data owner --> returns data identifier and resource
@router.post("", response_model=ResourceResponse)
async def create_resource(request: ResourceCreateRequest, db: Session = Depends(get_db), token=Depends(require_token("admin"))):
    try:
        resource_data = resources.create_resource(db, request)
        logger.debug(f"resource data: {resource_data}")

        # update spicedb relationships
        updates = [
            # Owner
            RelationshipUpdate(
                operation=RelationshipUpdate.OPERATION_TOUCH,
                relationship=Relationship(
                    resource=ObjectReference(object_type="resource", object_id=str(resource_data.resource_id)),
                    relation="owner",
                    subject=SubjectReference(object=ObjectReference(object_type="user", object_id=str(request.owner_id))),
                ),
            ),
            # Tenant link
            RelationshipUpdate(
                operation=RelationshipUpdate.OPERATION_TOUCH,
                relationship=Relationship(
                    resource=ObjectReference(object_type="resource", object_id=str(resource_data.resource_id)),
                    relation="tenant",
                    subject=SubjectReference(object=ObjectReference(object_type="tenant", object_id=str(request.tenant_id))),
                ),
            ),
        ]

        client.WriteRelationships(
            WriteRelationshipsRequest(updates=updates)
        )
        
        return ResourceResponse(data=resource_data, success=True) 
    
    except IntegrityError as e:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Resource already exists or violates constraints."}
        )
    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Unexpected error occurred", "detail": str(e)}
        )


# delete relationship that give subject permission to do scope
@router.delete("/{resource_id}/permissions/{subject_id}",)
async def delete_permission(
    resource_id: UUID,
    subject_id: UUID,
    scope: PermissionScope = Query(...),
    token=Depends(require_token("admin"))
    ):
    try:
        relation = "viewer" if scope == PermissionScope.read else "editor"

        updates = [
            RelationshipUpdate(
                operation=RelationshipUpdate.Operation.OPERATION_DELETE,
                relationship=Relationship(
                    resource=ObjectReference(
                        object_type="resource",
                        object_id=str(resource_id),
                    ),
                    relation=relation,
                    subject=SubjectReference(
                        object=ObjectReference(
                            object_type="user",
                            object_id=str(subject_id),
                        )
                    ),
                ),
            )
        ]

        client.WriteRelationships(
            WriteRelationshipsRequest(updates=updates)
        )

        return {
            "message": "Permission deleted successfully",
            "resource_id": str(resource_id),
            "subject_id": str(subject_id),
            "scope": scope.value,
            "relation": relation,
        }

    except Exception as e:
        logger.exception("Failed to remove permission")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete permission: {str(e)}",
        )


# get permissions for the selected resource
@router.get("/{resource_id}/permissions",)
async def get_resource_permission(
    resource_id: UUID,
    # scope: PermissionScope = Query(...),
    token=Depends(require_token("admin"))
    ):
    try:

        request = ReadRelationshipsRequest(
            relationship_filter=RelationshipFilter(
                resource_type="resource",
                optional_resource_id=str(resource_id),
            )
        )

        permissions = []

        # streaming API
        for resp in client.ReadRelationships(request):
            rel = resp.relationship

            logger.debug(f"relation: {rel}")

            permissions.append({
                "resource_type": rel.resource.object_type,
                "resource_id": rel.resource.object_id,
                "relation": rel.relation,
                "subject_type": rel.subject.object.object_type,
                "subject_id": rel.subject.object.object_id,
            })

        return {
            "resource_id": str(resource_id),
            "permissions": permissions,
        }

    except Exception as e:
        logger.exception("Failed to remove permission")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete permission: {str(e)}",
        )


@router.get("/{resource_id}")
async def get_resource(resource_id: str, db: Session = Depends(get_db), token=Depends(require_token("admin"))):
    try:
        resource = resources.get_resource(db, resource_id=resource_id)

        logger.info(f"response: {resource}")

        return ResourceResponse(data=resource, success=True) 
    
    except Exception as e:
        logger.exception("Failed to remove permission")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete permission: {str(e)}",
        )


# @router.get("/{resource_id}/logs")
# async def get_resource_logs(resource_id: str, token=Depends(require_token("admin"))):
#     response = await kc.get_resource_logs(resource_id)

#     logger.info(f"response: {response}")


#     if response.get("success"):
#         return JSONResponse(
#             content=response,
#             status_code=status.HTTP_200_OK
#         )
#     else:
#         return JSONResponse(
#             content=response,
#             status_code=response.get("status", status.HTTP_400_BAD_REQUEST)
#         )


@router.get("/{resource_id}/consents")
async def get_resource_consents(resource_id: str, db: Session = Depends(get_db), token=Depends(require_token("admin"))):
    try:
        response = resources.get_resource_consents(db, resource_id)
        consent_data_list = [ConsentData.model_validate(r) for r in response]
        return ConsentListResponse(data=consent_data_list, success=True)
    
    except Exception as e:
        logger.exception("Failed to get consents for selected resource_id")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get consents for selected resource_id: {str(e)}",
        )


# @router.delete("/{resource_id}")
# async def delete_resource(resource_id, token=Depends(require_token("admin"))):
#     response = await kc.delete_resource(resource_id=resource_id)
    
#     logger.info(f"response: {response}")

#     if response.get("success"):
#         return JSONResponse(
#             content={
#                 "message": "Resource deleted"
#             },
#             status_code=status.HTTP_200_OK
#         )
#     else:
#         return JSONResponse(
#             content={
#                 "error": "Failed to delete resource",
#                 "details": response.get("error")
#             },
#             status_code=response.get("status", status.HTTP_400_BAD_REQUEST)
        # )