from pathlib import Path
from typing import Any

import joblib
import pandas as pd


ML_DIR = Path(__file__).resolve().parent
NUMERIC_COLUMNS = ["tenure", "MonthlyCharges", "TotalCharges", "charges_per_tenure", "nb_services"]
BINARY_COLUMNS = [
    "gender",
    "Partner",
    "Dependents",
    "PhoneService",
    "PaperlessBilling",
]
SERVICE_COLUMNS = [
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
]
CATEGORICAL_COLUMNS = [
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "PaymentMethod",
]


def load_pickle(name: str) -> Any:
    for base_dir in [ML_DIR, *ML_DIR.parents]:
        path = base_dir / name
        if path.exists():
            return joblib.load(path)
    raise FileNotFoundError(
        f"Artefact ML introuvable: {name}. Place-le dans app/ml/ ou génère-le à la racine avec model.py."
    )


def _yes_no(value: str | int | bool | None) -> int:
    return 1 if value in ("Yes", "Male", 1, True) else 0


def preprocess_client(client: dict, scaler: Any, feature_names: list[str]) -> pd.DataFrame:
    raw = {k: v for k, v in client.items() if k not in {"_id", "id"}}
    df = pd.DataFrame([raw])

    df["TotalCharges"] = pd.to_numeric(df.get("TotalCharges", 0), errors="coerce").fillna(0)
    df["tenure"] = pd.to_numeric(df.get("tenure", 0), errors="coerce").fillna(0)
    df["MonthlyCharges"] = pd.to_numeric(df.get("MonthlyCharges", 0), errors="coerce").fillna(0)
    df["charges_per_tenure"] = df["MonthlyCharges"] / (df["tenure"] + 1)
    df["nb_services"] = df.apply(
        lambda row: sum(row[col] not in ["No", "No phone service", "No internet service"] for col in SERVICE_COLUMNS),
        axis=1,
    )
    df["senior_no_support"] = ((df["SeniorCitizen"] == 1) & (df["TechSupport"] == "No")).astype(int)
    df["monthly_electronic"] = (
        (df["Contract"] == "Month-to-month") & (df["PaymentMethod"] == "Electronic check")
    ).astype(int)
    df["is_new_client"] = (df["tenure"] <= 6).astype(int)

    df["gender"] = df["gender"].map({"Female": 0, "Male": 1}).fillna(0).astype(int)
    for col in ["Partner", "Dependents", "PhoneService", "PaperlessBilling"]:
        df[col] = df[col].apply(_yes_no).astype(int)
    df["Contract"] = df["Contract"].map({"Month-to-month": 0, "One year": 1, "Two year": 2}).fillna(0).astype(int)

    df = pd.get_dummies(df, columns=[c for c in CATEGORICAL_COLUMNS if c in df.columns], drop_first=True, dtype=int)
    for column in feature_names:
        if column not in df.columns:
            df[column] = 0
    df = df[feature_names]

    numeric_to_scale = [c for c in NUMERIC_COLUMNS if c in df.columns]
    if numeric_to_scale:
        df[numeric_to_scale] = scaler.transform(df[numeric_to_scale])
    return df


def risk_level(score: float) -> str:
    if score >= 0.8:
        return "critique"
    if score >= 0.6:
        return "élevé"
    if score >= 0.35:
        return "modéré"
    return "faible"
