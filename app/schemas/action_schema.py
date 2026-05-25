from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ActionCreate(BaseModel):
    client_id: str
    type_action: str
    description: str
    note: str | None = None
    priorite: Literal["urgent", "important", "optionnel"] = "important"
    resultat: Literal["succes", "neutre", "echec"] | None = None
    date_suivi: datetime | None = None


class ActionUpdate(BaseModel):
    type_action: str | None = None
    description: str | None = None
    note: str | None = None
    statut: Literal["en_attente", "faite", "annulee"] | None = None
    priorite: Literal["urgent", "important", "optionnel"] | None = None
    resultat: Literal["succes", "neutre", "echec"] | None = None
    date_suivi: datetime | None = None


class ActionResponse(BaseModel):
    id: str
    client_id: str
    commercial_id: str
    type_action: str
    description: str
    note: str | None = None
    priorite: Literal["urgent", "important", "optionnel"] = "important"
    resultat: Literal["succes", "neutre", "echec"] | None = None
    statut: Literal["en_attente", "faite", "annulee"]
    date_suivi: datetime | None = None
    created_at: datetime
    updated_at: datetime
