from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


Role = Literal["admin", "manager", "commercial"]


class UserInDB(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: EmailStr
    nom: str
    prenom: str
    role: Role = "commercial"
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
