from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.schemas.user_schema import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.auth_service import (
    authenticate_user,
    build_token_response,
    change_password,
    register_user,
    request_password_reset,
    reset_password,
)
from app.utils.dependencies import get_current_user


router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(payload: UserCreate, db: AsyncIOMotorDatabase = Depends(get_database)):
    return await register_user(db, payload)


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db: AsyncIOMotorDatabase = Depends(get_database)):
    user = await authenticate_user(db, payload.email, payload.password)
    return build_token_response(user)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncIOMotorDatabase = Depends(get_database)):
    return await request_password_reset(db, payload)


@router.post("/reset-password")
async def reset_user_password(payload: ResetPasswordRequest, db: AsyncIOMotorDatabase = Depends(get_database)):
    return await reset_password(db, payload)


@router.post("/change-password")
async def change_user_password(
    payload: ChangePasswordRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    return await change_password(db, current_user["id"], payload)


@router.get("/me", response_model=UserResponse)
async def me(current_user: dict = Depends(get_current_user)):
    return current_user
