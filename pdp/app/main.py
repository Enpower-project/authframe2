from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
import logging
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.crud import users
from app.crud import resources
from app.utils.audit import audit_logger_middleware, start_audit_worker

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


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # await start_audit_worker()
    yield


# start app
app = FastAPI(lifespan=lifespan, debug=True)

# app.middleware("http")(audit_logger_middleware)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


SPICEDB_TOKEN = "supersecretkey"
# client = Client("spicedb:50051", bearer_token_credentials(SPICEDB_TOKEN))
client = InsecureClient("spicedb:50051", SPICEDB_TOKEN)



@app.api_route("{remainder:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def check_permission(remainder: str, request: Request, db: Session = Depends(get_db)):

    headers = dict(request.headers)
    logger.debug(f"Headers: {headers}")

    logger.debug(f"requested path: {remainder}")

    # {
    #     'host': 'localhost:8080', 
    #     'content-length': '0', 
    #     'x-original-method': 'GET', 
    #     'x-sub': 'b8df0e6f-6a9b-4413-9577-716098b67315', 
    #     'x-username': 'bob', 
    #     'x-request-id': 'f05573f8-9ab9-4197-adf3-19803f50f24d', 
    #     'x-envoy-internal': 'true', 
    #     'x-envoy-expected-rq-timeout-ms': '1000'
    #     }

    allowed = False
    reason = "not authorized"
    
    # get IDP user ID
    idp_user_id = headers.get("x-sub")
    logger.debug(f"idp_user_id: {idp_user_id}")

    # action extraction
    method = headers.get("x-original-method")
    logger.debug(f"method: {method}")
    if "GET" == method:
        action = "read"
    else:
        action = "edit"

    # request ID
    request_id = headers.get("x-request-id")
    logger.debug(f"request_id: {request_id}")

    # get internal principal_id for authorization check
    principal_id = users.get_user_principal_id(db, idp_user_id)
    logger.debug(f"principal_id: {principal_id}")

    # get resource ID
    resource_id = resources.get_resource_by_url(db, remainder)
    logger.debug(f"resource_id: {resource_id}")

    # get tenant

    # prevent None being valid if registered as principal ID or resource ID
    if (None == principal_id) or (None == resource_id):
        allowed = False
        reason = "not authorized"
    else:
        # check permission
        resp = client.CheckPermission(
            CheckPermissionRequest(
                resource=ObjectReference(
                    object_type="resource",
                    object_id=str(resource_id)
                ),
                permission=action,
                subject=SubjectReference(
                    object=ObjectReference(
                        object_type="user",
                        object_id=str(principal_id)
                    )
                ),
            )
        )

        if resp.permissionship == CheckPermissionResponse.PERMISSIONSHIP_HAS_PERMISSION:
            allowed = True
            reason = "authorized"
            logger.debug("Access allowed")
        else:
            logger.debug("Access denied")
            reason = "unauthorized"
    

    if allowed:
        return JSONResponse(
            status_code=200,
            content={"decision": "allow"},
            headers={
            }
        )
    else:
        return JSONResponse(status_code=403, content={"decision": "deny", "reason": reason})


@app.get("/health", summary="Health check")
async def health_check():
    """
    Simple liveness/readiness endpoint for Envoy and monitoring.
    """
    return JSONResponse(content={"status": "ok"}, status_code=200)





