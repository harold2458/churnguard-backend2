from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.models.client_model import ClientInDB
from app.schemas.client_schema import ClientCreate, ClientResponse, ClientUpdate
from app.services.recommendation_service import generate_recommendations
from app.utils.dependencies import get_current_user
from app.utils.object_id import serialize_doc, serialize_docs


router = APIRouter(prefix="/clients", tags=["Clients"], dependencies=[Depends(get_current_user)])


@router.post("", response_model=ClientResponse, status_code=201)
async def create_client(payload: ClientCreate, db: AsyncIOMotorDatabase = Depends(get_database)):
    doc = ClientInDB(**payload.model_dump()).model_dump()
    result = await db.clients.insert_one(doc)
    return serialize_doc(await db.clients.find_one({"_id": result.inserted_id}))


@router.get("", response_model=list[ClientResponse])
async def list_clients(
    search: str | None = None,
    niveau_risque: str | None = None,
    contract: str | None = Query(default=None, alias="type_contrat"),
    tenure_min: int | None = None,
    tenure_max: int | None = None,
    skip: int = 0,
    limit: int = Query(50, le=200),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    query: dict = {}
    if search:
        query["$or"] = [
            {"nom": {"$regex": search, "$options": "i"}},
            {"prenom": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"telephone": {"$regex": search, "$options": "i"}},
        ]
    if niveau_risque:
        query["niveau_risque"] = niveau_risque
    if contract:
        query["Contract"] = contract
    if tenure_min is not None or tenure_max is not None:
        query["tenure"] = {}
        if tenure_min is not None:
            query["tenure"]["$gte"] = tenure_min
        if tenure_max is not None:
            query["tenure"]["$lte"] = tenure_max

    docs = await db.clients.find(query).skip(skip).limit(limit).sort("created_at", -1).to_list(limit)
    return serialize_docs(docs)


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(client_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    if not ObjectId.is_valid(client_id):
        raise HTTPException(status_code=400, detail="ID client invalide")
    client = await db.clients.find_one({"_id": ObjectId(client_id)})
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")
    return serialize_doc(client)


@router.get("/{client_id}/shap")
async def get_client_shap(client_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    if not ObjectId.is_valid(client_id):
        raise HTTPException(status_code=400, detail="ID client invalide")
    client = await db.clients.find_one({"_id": ObjectId(client_id)})
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")
    history = await db.historique_scores.find_one({"client_id": client_id}, sort=[("date_prediction", -1)])
    if not history:
        raise HTTPException(status_code=404, detail="Aucune explication SHAP disponible pour ce client")

    reasons = history.get("top_raisons_shap", [])
    return {
        "client_id": client_id,
        "client_nom": f"{client.get('prenom', '')} {client.get('nom', '')}".strip(),
        "score": history.get("score"),
        "niveau": history.get("niveau"),
        "date_prediction": history.get("date_prediction"),
        "facteurs": [
            {
                "feature": item.get("feature"),
                "value": item.get("valeur"),
                "shap_value": item.get("impact"),
                "french_label": _feature_label(item.get("feature", "")),
                "sens": "augmente_risque" if item.get("impact", 0) > 0 else "diminue_risque",
            }
            for item in reasons
        ],
    }


def _feature_label(feature: str) -> str:
    labels = {
        "Contract": "Type de contrat",
        "tenure": "Ancienneté",
        "MonthlyCharges": "Charges mensuelles",
        "TotalCharges": "Charges totales",
        "PaymentMethod_Electronic check": "Paiement par chèque électronique",
        "InternetService_Fiber optic": "Internet fibre optique",
        "charges_per_tenure": "Charges rapportées à l'ancienneté",
        "nb_services": "Nombre de services actifs",
    }
    return labels.get(feature, feature.replace("_", " "))


@router.get("/{client_id}/profile")
async def get_client_profile(client_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    if not ObjectId.is_valid(client_id):
        raise HTTPException(status_code=400, detail="ID client invalide")
    client = await db.clients.find_one({"_id": ObjectId(client_id)})
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")
    history = await db.historique_scores.find_one({"client_id": client_id}, sort=[("date_prediction", -1)])
    behaviors = await db.behaviors.find({"client_id": client_id}).sort("date_enregistrement", -1).limit(6).to_list(6)
    actions = await db.actions.find({"client_id": client_id}).sort("created_at", -1).limit(20).to_list(20)
    alerts = await db.alertes.find({"client_id": client_id}).sort("created_at", -1).limit(20).to_list(20)
    recommendations = history.get("recommandations") if history else generate_recommendations(client, behaviors[0] if behaviors else None)
    return {
        "client": serialize_doc(client),
        "derniere_prediction": serialize_doc(history) if history else None,
        "recommandations": recommendations,
        "top_raisons_shap": history.get("top_raisons_shap", []) if history else [],
        "behaviors": serialize_docs(behaviors),
        "actions": serialize_docs(actions),
        "alertes": serialize_docs(alerts),
    }


@router.get("/{client_id}/recommendations")
async def get_client_recommendations(client_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    if not ObjectId.is_valid(client_id):
        raise HTTPException(status_code=400, detail="ID client invalide")
    client = await db.clients.find_one({"_id": ObjectId(client_id)})
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")
    history = await db.historique_scores.find_one({"client_id": client_id}, sort=[("date_prediction", -1)])
    behavior = await db.behaviors.find_one({"client_id": client_id}, sort=[("date_enregistrement", -1)])
    recommandations = history.get("recommandations") if history else generate_recommendations(client, behavior)
    return {
        "client_id": client_id,
        "score": history.get("score") if history else client.get("score_churn"),
        "niveau": history.get("niveau") if history else client.get("niveau_risque"),
        "recommandations": [
            {"description": item, "priorite": _recommendation_priority(item), "statut": "a_faire"}
            for item in recommandations
        ],
    }


def _recommendation_priority(text: str) -> str:
    lowered = text.lower()
    if "réclamations" in lowered or "retards" in lowered or "appel" in lowered:
        return "urgent"
    if "contrat" in lowered or "assistance" in lowered:
        return "important"
    return "optionnel"


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(client_id: str, payload: ClientUpdate, db: AsyncIOMotorDatabase = Depends(get_database)):
    if not ObjectId.is_valid(client_id):
        raise HTTPException(status_code=400, detail="ID client invalide")
    data = payload.model_dump(exclude_unset=True)
    data["updated_at"] = datetime.now(timezone.utc)
    await db.clients.update_one({"_id": ObjectId(client_id)}, {"$set": data})
    client = await db.clients.find_one({"_id": ObjectId(client_id)})
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")
    return serialize_doc(client)


@router.delete("/{client_id}", status_code=204)
async def delete_client(client_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    if not ObjectId.is_valid(client_id):
        raise HTTPException(status_code=400, detail="ID client invalide")
    result = await db.clients.delete_one({"_id": ObjectId(client_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Client introuvable")
