from datetime import datetime, timezone

import pytest


pytestmark = pytest.mark.asyncio


ADMIN_PAYLOAD = {
    "email": "admin@example.com",
    "nom": "Admin",
    "prenom": "Test",
    "password": "password123",
    "role": "admin",
}


CLIENT_PAYLOAD = {
    "nom": "Risk",
    "prenom": "High",
    "email": "risk.high@example.com",
    "telephone": "+2290199999999",
    "gender": "Female",
    "SeniorCitizen": 1,
    "Partner": "No",
    "Dependents": "No",
    "tenure": 1,
    "PhoneService": "Yes",
    "MultipleLines": "Yes",
    "InternetService": "Fiber optic",
    "OnlineSecurity": "No",
    "OnlineBackup": "No",
    "DeviceProtection": "No",
    "TechSupport": "No",
    "StreamingTV": "No",
    "StreamingMovies": "No",
    "Contract": "Month-to-month",
    "PaperlessBilling": "Yes",
    "PaymentMethod": "Electronic check",
    "MonthlyCharges": 105.5,
    "TotalCharges": 105.5,
    "statut_actif": True,
}


async def _auth_headers(api_client):
    await api_client.post("/api/auth/register", json=ADMIN_PAYLOAD)
    response = await api_client.post(
        "/api/auth/login",
        json={"email": ADMIN_PAYLOAD["email"], "password": ADMIN_PAYLOAD["password"]},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_register_login_and_me(api_client):
    response = await api_client.post("/api/auth/register", json=ADMIN_PAYLOAD)
    assert response.status_code == 201
    assert response.json()["role"] == "admin"

    response = await api_client.post(
        "/api/auth/login",
        json={"email": ADMIN_PAYLOAD["email"], "password": ADMIN_PAYLOAD["password"]},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    response = await api_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == ADMIN_PAYLOAD["email"]


async def test_forgot_and_reset_password(api_client):
    await api_client.post("/api/auth/register", json=ADMIN_PAYLOAD)

    response = await api_client.post("/api/auth/forgot-password", json={"email": ADMIN_PAYLOAD["email"]})
    assert response.status_code == 200
    reset_token = response.json()["reset_token"]
    assert reset_token

    response = await api_client.post(
        "/api/auth/reset-password",
        json={"token": reset_token, "new_password": "newpassword123"},
    )
    assert response.status_code == 200

    response = await api_client.post(
        "/api/auth/login",
        json={"email": ADMIN_PAYLOAD["email"], "password": ADMIN_PAYLOAD["password"]},
    )
    assert response.status_code == 401

    response = await api_client.post(
        "/api/auth/login",
        json={"email": ADMIN_PAYLOAD["email"], "password": "newpassword123"},
    )
    assert response.status_code == 200


async def test_change_password_and_admin_invite(api_client):
    headers = await _auth_headers(api_client)

    response = await api_client.post(
        "/api/auth/change-password",
        json={"old_password": ADMIN_PAYLOAD["password"], "new_password": "changed123"},
        headers=headers,
    )
    assert response.status_code == 200

    response = await api_client.post(
        "/api/admin/users/invite",
        json={"email": "commercial@example.com", "role": "commercial", "nom": "Com", "prenom": "Mercial"},
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["invite_token"]
    assert body["user"]["role"] == "commercial"


async def test_client_crud_and_filters(api_client):
    headers = await _auth_headers(api_client)

    response = await api_client.post("/api/clients", json=CLIENT_PAYLOAD, headers=headers)
    assert response.status_code == 201
    client_id = response.json()["id"]

    response = await api_client.get("/api/clients?search=risk&type_contrat=Month-to-month", headers=headers)
    assert response.status_code == 200
    assert response.json()[0]["id"] == client_id

    response = await api_client.patch(f"/api/clients/{client_id}", json={"nom": "RiskUpdated"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["nom"] == "RiskUpdated"


async def test_prediction_alert_and_dashboard(api_client, monkeypatch):
    headers = await _auth_headers(api_client)
    client_response = await api_client.post("/api/clients", json=CLIENT_PAYLOAD, headers=headers)
    client_id = client_response.json()["id"]

    behavior_payload = {
        "client_id": client_id,
        "frequence_utilisation": 1,
        "nombre_reclamations": 7,
        "retards_paiement": 4,
        "interactions_service_client": 9,
        "baisse_activite": True,
        "historique_consommation": [105, 88, 62, 35],
    }
    response = await api_client.post("/api/behaviors", json=behavior_payload, headers=headers)
    assert response.status_code == 201

    async def fake_predict_client_churn(db, target_client_id):
        now = datetime.now(timezone.utc)
        reasons = [{"feature": "Contract", "impact": 0.7, "valeur": "Month-to-month"}]
        recommendations = ["Proposer un contrat annuel avec une réduction de fidélité."]
        await db.historique_scores.insert_one(
            {
                "client_id": target_client_id,
                "score": 0.72,
                "niveau": "élevé",
                "top_raisons_shap": reasons,
                "recommandations": recommendations,
                "date_prediction": now,
            }
        )
        await db.clients.update_one(
            {"_id": client_response.json()["id"]},
            {"$set": {"score_churn": 0.72, "niveau_risque": "élevé", "derniere_prediction": now}},
        )
        await db.alertes.insert_one(
            {
                "client_id": target_client_id,
                "client_nom": "High Risk",
                "niveau": "élevé",
                "motif": "Score churn élevé: 72.0%",
                "score_avant": None,
                "score_apres": 0.72,
                "lue": False,
                "traitee": False,
                "traitee_par": None,
                "traitee_le": None,
                "created_at": now,
            }
        )
        return {
            "client_id": target_client_id,
            "score_churn": 0.72,
            "score_pct": 72.0,
            "niveau_risque": "élevé",
            "decision": "client à risque",
            "top_raisons_shap": reasons,
            "recommandations": recommendations,
        }

    monkeypatch.setattr("app.routes.prediction_routes.predict_client_churn", fake_predict_client_churn)

    response = await api_client.post(f"/api/predictions/client/{client_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["niveau_risque"] == "élevé"

    response = await api_client.get("/api/alerts?non_traitees=true", headers=headers)
    assert response.status_code == 200
    alert = response.json()[0]
    assert alert["score_apres"] == 0.72

    response = await api_client.patch(f"/api/alerts/{alert['id']}/read", headers=headers)
    assert response.status_code == 200
    assert response.json()["lue"] is True

    response = await api_client.get("/api/dashboard/stats", headers=headers)
    assert response.status_code == 200
    assert response.json()["nombre_clients_a_risque"] == 1

    response = await api_client.get("/api/dashboard/home", headers=headers)
    assert response.status_code == 200
    assert response.json()["kpis"]["mrr_a_risque"] > 0

    action_payload = {
        "client_id": client_id,
        "type_action": "appel",
        "description": "Appel de suivi",
        "priorite": "urgent",
        "date_suivi": "2026-05-10T10:00:00Z",
    }
    response = await api_client.post("/api/actions", json=action_payload, headers=headers)
    assert response.status_code == 201

    response = await api_client.get("/api/actions/board", headers=headers)
    assert response.status_code == 200
    assert response.json()["compteurs"]["urgentes"] == 1

    response = await api_client.get(f"/api/clients/{client_id}/shap", headers=headers)
    assert response.status_code == 200
    assert response.json()["facteurs"][0]["french_label"] == "Type de contrat"

    response = await api_client.get(f"/api/clients/{client_id}/profile", headers=headers)
    assert response.status_code == 200
    assert response.json()["client"]["id"] == client_id

    response = await api_client.get(f"/api/clients/{client_id}/recommendations", headers=headers)
    assert response.status_code == 200
    assert response.json()["recommandations"][0]["priorite"] in {"urgent", "important", "optionnel"}

    response = await api_client.get("/api/alerts/summary/counts", headers=headers)
    assert response.status_code == 200
    assert response.json()["non_traitees"] == 1

    response = await api_client.get("/api/search?q=Risk", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["clients"]) == 1

    response = await api_client.get("/api/reports/summary", headers=headers)
    assert response.status_code == 200
    assert "par_contrat" in response.json()

    response = await api_client.get("/api/reports/export?format=csv", headers=headers)
    assert response.status_code == 200
    assert "score_churn" in response.text

    response = await api_client.get("/api/history/global", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] >= 2


async def test_health_and_notifications(api_client, fake_db):
    headers = await _auth_headers(api_client)
    response = await api_client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    await fake_db.notifications.insert_one(
        {
            "type": "alerte_client",
            "titre": "Test",
            "description": "Notification de test",
            "client_id": "client-id",
            "lue": False,
            "created_at": datetime.now(timezone.utc),
        }
    )
    response = await api_client.get("/api/notifications?unread_only=true", headers=headers)
    assert response.status_code == 200
    notification_id = response.json()[0]["id"]

    response = await api_client.patch(f"/api/notifications/{notification_id}/read", headers=headers)
    assert response.status_code == 200
    assert response.json()["lue"] is True
