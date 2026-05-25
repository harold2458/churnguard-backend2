# ChurnGuard Backend

Backend FastAPI pour le mémoire **Système intelligent d'analyse comportementale anti-churn client**.

## Fonctionnalités

- Authentification JWT avec rôles `admin`, `manager`, `commercial`
- Mot de passe oublié, changement de mot de passe et invitations admin
- CRUD clients avec recherche et filtres
- Stockage MongoDB Atlas via Motor async
- Analyse comportementale client
- Prédiction du churn avec modèle XGBoost `.pkl`
- Explicabilité SHAP / TreeSHAP
- Recommandations intelligentes de fidélisation
- Historique des prédictions
- Alertes automatiques pour risques `élevé` et `critique`
- Actions commerciales
- Dashboard et routes admin
- Rapports/export CSV, recherche globale, notifications et historique global
- API unique pour Flutter et Next.js

## Installation

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Renseigner ensuite `MONGO_URI` et `JWT_SECRET_KEY` dans `.env`.

## Fichiers ML attendus

Placer les fichiers suivants dans `backend/app/ml/` :

- `churn_model.pkl`
- `scaler.pkl`
- `feature_names.pkl`
- `model_metrics.pkl` optionnel

Le backend stocke les données clients brutes dans MongoDB. L'encodage, le feature engineering et l'alignement avec `feature_names.pkl` sont exécutés uniquement pendant la prédiction dans `app/ml/preprocessing.py`.

## Lancement

```bash
uvicorn app.main:app --reload
```

Swagger sera disponible sur :

```text
http://127.0.0.1:8000/docs
```

## Routes principales

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/forgot-password`
- `POST /api/auth/reset-password`
- `POST /api/auth/change-password`
- `POST /api/clients`
- `GET /api/clients`
- `GET /api/clients/{client_id}`
- `PATCH /api/clients/{client_id}`
- `DELETE /api/clients/{client_id}`
- `POST /api/behaviors`
- `GET /api/behaviors/client/{client_id}`
- `POST /api/predictions/client/{client_id}`
- `GET /api/alerts`
- `PATCH /api/alerts/{id}/read`
- `PATCH /api/alerts/{id}/done`
- `POST /api/actions`
- `GET /api/actions/client/{client_id}`
- `PATCH /api/actions/{id}/done`
- `GET /api/dashboard/stats`
- `GET /api/dashboard/home`
- `GET /api/clients/{id}/shap`
- `GET /api/clients/{id}/profile`
- `GET /api/clients/{id}/recommendations`
- `GET /api/alerts/summary/counts`
- `GET /api/actions/board`
- `GET /api/search?q=terme`
- `GET /api/notifications`
- `PATCH /api/notifications/{id}/read`
- `PATCH /api/notifications/read-all`
- `GET /api/history/global`
- `GET /api/reports/summary`
- `GET /api/reports/export?format=csv`
- `GET /api/reports/export?format=pdf`
- `GET /api/health`
- `GET /api/admin/users`
- `POST /api/admin/users/invite`
- `POST /api/admin/users/{id}/reset-password`
- `DELETE /api/admin/users/{id}`
- `GET /api/admin/model/metrics`

## Exemple de client

```json
{
  "nom": "Doe",
  "prenom": "John",
  "email": "john.doe@example.com",
  "telephone": "+2290100000000",
  "gender": "Male",
  "SeniorCitizen": 0,
  "Partner": "Yes",
  "Dependents": "No",
  "tenure": 12,
  "PhoneService": "Yes",
  "MultipleLines": "No",
  "InternetService": "Fiber optic",
  "OnlineSecurity": "No",
  "OnlineBackup": "Yes",
  "DeviceProtection": "No",
  "TechSupport": "No",
  "StreamingTV": "Yes",
  "StreamingMovies": "No",
  "Contract": "Month-to-month",
  "PaperlessBilling": "Yes",
  "PaymentMethod": "Electronic check",
  "MonthlyCharges": 89.9,
  "TotalCharges": 1078.8,
  "statut_actif": true
}
```

## Notes

- Les routes protégées utilisent `Authorization: Bearer <token>`.
- Les routes dashboard sont réservées à `admin` et `manager`.
- Les routes admin sont réservées à `admin`.
- `POST /api/admin/model/retrain` est un point d'extension pour brancher un pipeline de réentraînement externe.



Username: churnguard_user
Password: admin12345



{
  "email": "admin2@example.com",
  "nom": "Admin",
  "prenom": "Test",
  "password": "Harold123",
  "role": "admin"
}




{
  "email": "admin2@example.com",
  "password": "Harold123"
}

uvicorn app.main:app --reload
 