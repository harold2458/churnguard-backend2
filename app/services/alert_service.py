from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase


async def create_risk_alert(
    db: AsyncIOMotorDatabase,
    client: dict,
    old_score: float | None,
    new_score: float,
    level: str,
) -> None:
    if level not in {"élevé", "critique"}:
        return
    now = datetime.now(timezone.utc)
    client_id = str(client.get("_id") or client.get("id"))
    client_nom = f"{client.get('prenom', '')} {client.get('nom', '')}".strip()
    motif = f"Score churn {level}: {round(new_score * 100, 2)}%"
    await db.alertes.insert_one(
        {
            "client_id": client_id,
            "client_nom": client_nom,
            "niveau": level,
            "motif": motif,
            "score_avant": old_score,
            "score_apres": new_score,
            "lue": False,
            "traitee": False,
            "traitee_par": None,
            "traitee_le": None,
            "created_at": now,
        }
    )
    await db.notifications.insert_one(
        {
            "type": "alerte_client",
            "titre": f"Client {level}: {client_nom}",
            "description": motif,
            "client_id": client_id,
            "lue": False,
            "created_at": now,
        }
    )
