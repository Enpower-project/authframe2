# SPDX-License-Identifier: Apache-2.0
from contextlib import asynccontextmanager

from fastapi import FastAPI
# from app.api import consents, consent_requests
from app.api import resources
from app.api import tenants
from app.api import users
from app.api import permissions
from app.api import consents
from app.db.base import Base
from app.db.session import engine
import logging
from app.utils.audit import audit_logger_middleware, start_audit_worker

# from app.keycloak_instance import kc


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from app.keycloak_instance import kc


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Base.metadata.create_all(bind=engine)
    await kc.init()
    await start_audit_worker()
    yield


# start app
app = FastAPI(lifespan=lifespan)

app.middleware("http")(audit_logger_middleware)

# register routers
app.include_router(tenants.router)
app.include_router(resources.router)
app.include_router(users.router)
app.include_router(permissions.router)
app.include_router(consents.router)


