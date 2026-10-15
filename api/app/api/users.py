from fastapi import APIRouter, Depends
from fastapi import Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.auth.dependencies import require_token
from app.db.session import SessionLocal
from app.crud import users
from app.schemas.user import UserRequest, UserCreateDB, UserData, UserResponse, UserListResponse
import logging

from app.keycloak_instance import kc

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/users", tags=["users"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("")
async def get_users(token=Depends(require_token("admin"))):
    response = await kc.get_all_users()

    logger.info(f"users: {response}")

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
async def create_user(request: UserRequest, token=Depends(require_token("admin"))):
    logger.info(f"request_data: {request}")

    response = await kc.create_user(
        username=request.username,
        first_name=request.first_name,
        last_name=request.last_name,
        email=request.email,
        email_verified=request.email_verified,
        credentials=request.credentials,
        enabled=request.enabled)
    
    logger.info(f"user: {response}")

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


@router.get("/map", response_model=UserListResponse)
async def get_user_mapping(db: Session = Depends(get_db), token=Depends(require_token("admin"))):
    try:
        response = users.get_all_users(db)
        users_data_list = [UserData.model_validate(u) for u in response]
        return UserListResponse(data=users_data_list, success=True)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Unexpected error occurred", "detail": str(e)}
        )


@router.post("/map")
async def map_user(request: UserCreateDB, db: Session = Depends(get_db), token=Depends(require_token("admin"))):
    try:
        logger.info(f"request_data: {request}")

        # add subject map for the new user
        subject_map = users.create_subject_map(db, request)

        logger.info(f"subject_map: {subject_map}")

        return UserResponse(data=subject_map, success=True)
    
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Unexpected error occurred", "detail": str(e)}
        )



@router.get("/{user_id}")
async def get_user_by_id(user_id: str, token=Depends(require_token("admin"))):
    response = await kc.get_user_by_id(user_id)

    logger.info(f"user: {response}")

    return JSONResponse(
        content=response,
        status_code=status.HTTP_200_OK
    )


# get resources for specific user with {user_id}
# @router.get("/{user_id}/resources")
# async def get_user_resources(user_id: str, token=Depends(require_token("admin"))):
#     response = await kc.get_user_by_id(user_id)

#     logger.info(f"user: {response}")

#     return JSONResponse(
#         content=response,
#         status_code=status.HTTP_200_OK
#     )


@router.put("/{user_id}")
async def update_user(user_id, request: UserRequest, token=Depends(require_token("admin"))):
    response = await kc.update_user(
        user_id=user_id,
        username=request.username,
        first_name=request.first_name,
        last_name=request.last_name,
        email=request.email,
        email_verified=request.email_verified,
        credentials=request.credentials,
        enabled=request.enabled)
    
    logger.info(f"response: {response}")

    if response.get("success"):
        return JSONResponse(
            content={
                "message": "User updated"
            },
            status_code=status.HTTP_200_OK
        )
    else:
        return JSONResponse(
            content={
                "error": "Failed to update user",
                "details": response.get("error")
            },
            status_code=response.get("status", status.HTTP_400_BAD_REQUEST)
        )


@router.delete("/{user_id}")
async def delete_user(user_id, token=Depends(require_token("admin"))):
    response = await kc.delete_user(user_id=user_id)
    
    logger.info(f"response: {response}")

    if response.get("success"):
        return JSONResponse(
            content={
                "message": "User deleted"
            },
            status_code=status.HTTP_200_OK
        )
    else:
        return JSONResponse(
            content={
                "error": "Failed to delete user",
                "details": response.get("error")
            },
            status_code=response.get("status", status.HTTP_400_BAD_REQUEST)
        )