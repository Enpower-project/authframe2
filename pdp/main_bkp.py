from contextlib import asynccontextmanager
from fastapi import FastAPI
import aiohttp
# import httpx
import grpc
from authzed.api.v1 import permission_service_pb2 as ps
from authzed.api.v1 import permission_service_pb2_grpc as psg
from authzed.api.v1 import core_pb2 as core
from app.schemas.pdp import Subject, Resource, DecisionRequest
# from app.api import consents, consent_requests
# from app.db.base import Base
# from app.db.session import engine
import logging
# from app.utils.audit import audit_logger_middleware, start_audit_worker

# from app.keycloak_instance import kc
# import app.api.users as users


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# from app.keycloak_instance import kc


@asynccontextmanager
async def lifespan(app: FastAPI):
    pass
    # Base.metadata.create_all(bind=engine)
    # await kc.init()
    # await start_audit_worker()
    yield


# start app
app = FastAPI(lifespan=lifespan)

# app.middleware("http")(audit_logger_middleware)

# SPICEDB_ADDR = "spicedb:50051"
OPA_URL = "http://opa:8181/v1/data/authz/allow"



channel = grpc.insecure_channel("spicedb:50051")
spicedb = psg.PermissionsServiceStub(channel)

def check_rebac(subject_id: str, resource: Resource, action: str):
    req = ps.CheckPermissionRequest(
        resource=core.ObjectReference(
            object_type=resource.type,
            object_id=f"{resource.tenant}/{resource.id}"
        ),
        permission=action,
        subject=core.SubjectReference(
            object=core.ObjectReference(object_type="user", object_id=subject_id)
        ),
    )
    resp = spicedb.CheckPermission(req)
    allowed = resp.permissionship == ps.CheckPermissionResponse.PERMISSIONSHIP_HAS_PERMISSION
    return allowed, resp.checked_at.token


async def check_abac(subject: dict, resource: dict, action: str, context: dict):
    """
    Performs ABAC authorization check against OPA using aiohttp.
    Returns the OPA policy 'result' (dict).
    """
    opa_input = {
        "subject": subject,
        "resource": resource,
        "action": action,
        "context": context
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(OPA_URL, json={"input": opa_input}) as resp:
            if resp.status != 200:
                body = await resp.text()
                raise RuntimeError(f"OPA request failed: {resp.status} {body}")

            data = await resp.json()
            return data.get("result")


@app.post("/v1/pdp")
async def decide(req: DecisionRequest):
    # 1. ReBAC
    allowed_rebac, zed_token = check_rebac(req.subject.id, req.resource, req.action)
    if not allowed_rebac:
        return {"effect": "Deny", "reason": "rebac_denied"}

    # 2. ABAC
    abac_result = await check_abac(req.subject.dict(), req.resource.dict(), req.action, req.context)
    if not abac_result.get("allow", False):
        return {
            "effect": "Deny",
            "reason": "abac_denied",
            "obligations": abac_result.get("obligations", {})
        }

    # 3. Permit
    return {
        "effect": "Permit",
        "reason": "rebac+abac",
        "obligations": abac_result.get("obligations", {}),
        "checked_at": {"zed_token": zed_token}
    }
# register routers
# app.include_router(members.router)
# app.include_router(grid_elements.router)
# app.include_router(service_points.router)
# app.include_router(meters.router)
# app.include_router(channels.router)


