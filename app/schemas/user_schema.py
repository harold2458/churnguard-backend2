from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


Role = Literal["admin", "manager", "commercial"]


class UserCreate(BaseModel):
    email: EmailStr
    nom: str
    prenom: str
    password: str = Field(min_length=8)
    role: Role = "commercial"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str
    reset_token: str | None = None


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)


class UserInviteRequest(BaseModel):
    email: EmailStr
    role: Role = "commercial"
    nom: str = "Invité"
    prenom: str = "Utilisateur"


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    nom: str
    prenom: str
    role: Role
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserRoleUpdate(BaseModel):
    role: Role
