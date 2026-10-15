from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.session import SessionLocal
from app.auth.dependencies import require_token
from app.schemas.permission import PermissionRequest
from fastapi import Depends
from fastapi.responses import JSONResponse
import json

from grpcutil import bearer_token_credentials

from authzed.api.v1 import (
    Client,
    InsecureClient,
    WriteRelationshipsRequest,
    WriteSchemaRequest,
    Relationship,
    RelationshipUpdate,
    ObjectReference,
    SubjectReference,
    CheckPermissionRequest,
    CheckPermissionResponse,
    ObjectReference,
    SubjectReference,
)

import logging

logger = logging.getLogger(__name__)

from app.keycloak_instance import kc


SPICEDB_TOKEN = "supersecretkey"
# client = Client("spicedb:50051", bearer_token_credentials(SPICEDB_TOKEN))
client = InsecureClient("spicedb:50051", SPICEDB_TOKEN)


router = APIRouter(prefix="/permissions", tags=["permissions"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("",)
async def set_permission(request: PermissionRequest, token=Depends(require_token("admin"))):
    try:   
        resource_id = request.resource_id
        subject_id = request.subject_id
        scope = request.scope
        if "read" == scope:  
            relation = "viewer"
        else:
            relation = "editor"

        logger.info(f"resource_id: {resource_id}, subject_id: {subject_id}, scope: {scope}")

        # -----------------------------------
        # set new relation to set permission
        # -----------------------------------
        updates = []
        updates += [
            RelationshipUpdate(
                operation=RelationshipUpdate.OPERATION_TOUCH,
                relationship=Relationship(
                    resource=ObjectReference(object_type="resource", object_id=str(resource_id)),
                    relation=relation,
                    subject=SubjectReference(object=ObjectReference(object_type="user", object_id=str(subject_id))),
                ),
            ),
        ]

        logger.info(f"updates: {updates}")

        client.WriteRelationships(request=WriteRelationshipsRequest(updates=updates))

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Permissions mapped"
                }
        )

    except Exception as e:
        logger.error(f"exception: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "message": "Unexpected error occurred", 
                "detail": str(e)
                }
        ) 
    

@router.get("",)
async def run_permissions(token=Depends(require_token("admin"))):
    try:
        BOB = "da2d6183-5325-47c7-97ad-89b5c15380ae"
        ALICE = "a07b36d9-79fa-4cf8-8e47-4681e1631390"
        DEMO_EC = "b39c7d64-95fa-487d-999b-e1a9211fd753"
        R1 = "55dbae4e-f536-476a-a0e9-c5a2e940bfd2"
        R2 = "8f25b079-125e-4fe5-83fb-a0af75b12165"
        R3 = "823eaf5b-3a17-494e-b653-ba0f057679f7"

        updates = []

        # -------------------------------
        # Tenant membership
        # -------------------------------
        updates += [
            # ALICE is admin of DEMO_EC
            RelationshipUpdate(
                operation=RelationshipUpdate.OPERATION_TOUCH,
                relationship=Relationship(
                    resource=ObjectReference(object_type="tenant", object_id=DEMO_EC),
                    relation="admin",
                    subject=SubjectReference(object=ObjectReference(object_type="user", object_id=ALICE)),
                ),
            ),
            # BOB is member of DEMO_EC
            RelationshipUpdate(
                operation=RelationshipUpdate.OPERATION_TOUCH,
                relationship=Relationship(
                    resource=ObjectReference(object_type="tenant", object_id=DEMO_EC),
                    relation="member",
                    subject=SubjectReference(object=ObjectReference(object_type="user", object_id=BOB)),
                ),
            ),
        ]

        # -------------------------------
        # R1 
        # -------------------------------
        updates += [
            # Owner
            RelationshipUpdate(
                operation=RelationshipUpdate.OPERATION_TOUCH,
                relationship=Relationship(
                    resource=ObjectReference(object_type="resource", object_id=R1),
                    relation="owner",
                    subject=SubjectReference(object=ObjectReference(object_type="user", object_id=ALICE)),
                ),
            ),
            # Tenant link
            RelationshipUpdate(
                operation=RelationshipUpdate.OPERATION_TOUCH,
                relationship=Relationship(
                    resource=ObjectReference(object_type="resource", object_id=R1),
                    relation="tenant",
                    subject=SubjectReference(object=ObjectReference(object_type="tenant", object_id=DEMO_EC)),
                ),
            ),
        ]

        # -------------------------------
        # R2 
        # -------------------------------
        updates += [
            # Owner
            RelationshipUpdate(
                operation=RelationshipUpdate.OPERATION_TOUCH,
                relationship=Relationship(
                    resource=ObjectReference(object_type="resource", object_id=R2),
                    relation="owner",
                    subject=SubjectReference(object=ObjectReference(object_type="user", object_id=ALICE)),
                ),
            ),
            # Tenant link
            RelationshipUpdate(
                operation=RelationshipUpdate.OPERATION_TOUCH,
                relationship=Relationship(
                    resource=ObjectReference(object_type="resource", object_id=R2),
                    relation="tenant",
                    subject=SubjectReference(object=ObjectReference(object_type="tenant", object_id=DEMO_EC)),
                ),
            ),
        ]

        # -------------------------------
        # R3 
        # -------------------------------
        updates += [
            # Owner
            RelationshipUpdate(
                operation=RelationshipUpdate.OPERATION_TOUCH,
                relationship=Relationship(
                    resource=ObjectReference(object_type="resource", object_id=R3),
                    relation="owner",
                    subject=SubjectReference(object=ObjectReference(object_type="user", object_id=ALICE)),
                ),
            ),
            # Tenant link
            RelationshipUpdate(
                operation=RelationshipUpdate.OPERATION_TOUCH,
                relationship=Relationship(
                    resource=ObjectReference(object_type="resource", object_id=R3),
                    relation="tenant",
                    subject=SubjectReference(object=ObjectReference(object_type="tenant", object_id=DEMO_EC)),
                ),
            ),
        ]

        client.WriteRelationships(request=WriteRelationshipsRequest(updates=updates))

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Permissions mapped"}
        )
    
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Unexpected error occurred", "detail": str(e)}
        )


@router.get("/schema",)
async def define_authzed_schema(token=Depends(require_token("admin"))):
    try:

        SCHEMA = """
            definition user {}

            definition tenant {
                relation admin: user
                relation member: user

                permission manage = admin
                permission view = admin + member
            }

            definition resource {
                relation owner: user
                relation tenant: tenant
                relation viewer: user
                relation editor: user

                permission read = owner + viewer + editor
                permission edit = owner + editor
            }
        """

        request = WriteSchemaRequest(schema=SCHEMA)
        client.WriteSchema(request=request)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Schema written"}
        )
    
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Unexpected error occurred", "detail": str(e)}
        )


# old schema with visibility
# define schema

# definition user {}

# definition tenant {
#     relation admin: user
#     relation member: user
#     permission manage = admin
#     permission view = admin + member
# }

# definition resource {
#     relation owner: user
#     relation tenant: tenant
#     relation viewer: user
#     relation visibility: visibility
#
#     permission read = 
#         owner
#         + viewer
#         + (tenant->member if visibility->tenant_access)
#         + (visibility->public_access)
#
#     permission edit = owner
# }

# definition visibility {
#     relation private_access: resource
#     relation tenant_access: resource
#     relation public_access: resource
# }



