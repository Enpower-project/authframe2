import os
import asyncio
from datetime import datetime, timezone
from fastapi import Request, Response
import jwt
import clickhouse_connect
from dotenv import load_dotenv

load_dotenv()

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST")
CLICKHOUSE_PORT = os.getenv("CLICKHOUSE_PORT")
USERNAME = os.getenv("CLICKHOUSE_DB_USER")
PASSWORD = os.getenv("CLICKHOUSE_DB_PASSWORD")
EVENT_DB = os.getenv("CLICKHOUSE_DB_NAME")
LOG_TABLE = os.getenv("CLICKHOUSE_LOG_TABLE")



audit_queue: asyncio.Queue = asyncio.Queue()

clickhouse_client = clickhouse_connect.get_client(
    host=CLICKHOUSE_HOST,
    port=CLICKHOUSE_PORT,
    username=USERNAME,
    password=PASSWORD,
    database=EVENT_DB
)


async def audit_logger_middleware(request: Request, call_next):
    # extract user info from token
    auth_header = request.headers.get("Authorization")
    user_info = {
        "user_id": None,
        "username": None,
        "email": None,
        "roles": []
    }

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            user_info = {
                "user_id": decoded.get("sub"),
                "username": decoded.get("preferred_username"),
                "email": decoded.get("email"),
                "roles": decoded.get("realm_access", {}).get("roles", [])
            }
        except Exception as e:
            user_info["email"] = f"token decode error: {e}"

    response: Response = await call_next(request)

    event = [
        datetime.now(timezone.utc),
        request.method,
        request.url.path,
        request.client.host if request.client else None,



        user_info["user_id"] or "",
        user_info["username"] or "",
        user_info["email"] or "",
        user_info["roles"],
        
        
        response.status_code,
        
    ]

    await audit_queue.put(event)
    return response


async def audit_worker(batch_size: int = 100, flush_interval: float = 1.0):
    buffer = []
    while True:
        try:
            event = await asyncio.wait_for(audit_queue.get(), timeout=flush_interval)
            buffer.append(event)
            if len(buffer) >= batch_size:
                flush_to_clickhouse(buffer)
                buffer.clear()
        except asyncio.TimeoutError:
            if buffer:
                flush_to_clickhouse(buffer)
                buffer.clear()


def flush_to_clickhouse(buffer):
    clickhouse_client.insert(
        LOG_TABLE, buffer,
        column_names=[
            "timestamp", "method", "requested_path", "host",
            "request_scope", "request_id", "jwt_subject", 
            "response_code", "decision", "reason"
        ]
    )


async def start_audit_worker():
    asyncio.create_task(audit_worker())