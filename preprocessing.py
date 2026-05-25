# ============================================================
#  SYSTÈME ANTI-CHURN — ÉTAPE 2 : PREPROCESSING
#  Dataset : IBM Telco Customer Churn
#  Auteur  : [Ton Nom]
# ============================================================

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from imblearn.over_sampling import SMOTE
import joblib
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("  PREPROCESSING DU DATASET TELCO CHURN")
print("=" * 60)


# ── 1. CHARGEMENT ────────────────────────────────────────────
df = pd.read_csv(r"C:\Users\USER-PC\Downloads\archive\WA_Fn-UseC_-Telco-Customer-Churn.csv")
print(f"\n✅ Dataset chargé : {df.shape[0]} lignes, {df.shape[1]} colonnes")


# ── 2. NETTOYAGE ─────────────────────────────────────────────
print("\n── Nettoyage ──────────────────────────────────────────")

# TotalCharges : convertir en numérique (quelques espaces vides)
df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')

# Valeurs manquantes après conversion
nb_null = df['TotalCharges'].isnull().sum()
print(f"  Valeurs manquantes TotalCharges : {nb_null}")

# Imputation par la médiane (clients avec tenure=0, probablement nouveaux)
df['TotalCharges'].fillna(df['TotalCharges'].median(), inplace=True)
print(f"  ✅ Imputées par la médiane")

# Supprimer customerID (identifiant non prédictif)
df.drop(columns=['customerID'], inplace=True)
print(f"  ✅ Colonne customerID supprimée")


# ── 3. FEATURE ENGINEERING ───────────────────────────────────
print("\n── Feature Engineering ────────────────────────────────")

# Feature 1 : Charge par mois d'ancienneté (ratio valeur/temps)
df['charges_per_tenure'] = df['MonthlyCharges'] / (df['tenure'] + 1)

# Feature 2 : Nombre de services souscrits
services = ['PhoneService', 'MultipleLines', 'InternetService',
            'OnlineSecurity', 'OnlineBackup', 'DeviceProtection',
            'TechSupport', 'StreamingTV', 'StreamingMovies']

def count_services(row):
    count = 0
    for s in services:
        if row[s] not in ['No', 'No phone service', 'No internet service']:
            count += 1
    return count

df['nb_services'] = df.apply(count_services, axis=1)

# Feature 3 : Client senior sans support technique (profil vulnérable)
df['senior_no_support'] = (
    (df['SeniorCitizen'] == 1) &
    (df['TechSupport'] == 'No')
).astype(int)

# Feature 4 : Contrat mensuel + paiement électronique (double risque)
df['monthly_electronic'] = (
    (df['Contract'] == 'Month-to-month') &
    (df['PaymentMethod'] == 'Electronic check')
).astype(int)

# Feature 5 : Client récent (< 6 mois) — zone critique
df['is_new_client'] = (df['tenure'] <= 6).astype(int)

print(f"  ✅ 5 nouvelles features créées :")
print(f"     → charges_per_tenure")
print(f"     → nb_services")
print(f"     → senior_no_support")
print(f"     → monthly_electronic")
print(f"     → is_new_client")


# ── 4. ENCODAGE DES VARIABLES CATÉGORIELLES ──────────────────
print("\n── Encodage ───────────────────────────────────────────")

# Variable cible
df['Churn'] = (df['Churn'] == 'Yes').astype(int)
print(f"  ✅ Churn encodé : Yes=1, No=0")

# Variables binaires (Yes/No)
binary_cols = ['gender', 'Partner', 'Dependents', 'PhoneService',
               'PaperlessBilling']
binary_map = {'Yes': 1, 'No': 0, 'Female': 0, 'Male': 1}
for col in binary_cols:
    df[col] = df[col].map(binary_map)
print(f"  ✅ Variables binaires encodées : {binary_cols}")

# Variables ordinales
contract_map = {'Month-to-month': 0, 'One year': 1, 'Two year': 2}
df['Contract'] = df['Contract'].map(contract_map)
print(f"  ✅ Contract encodé : 0=mensuel, 1=annuel, 2=biannuel")

# One-Hot Encoding pour variables nominales multi-classes
ohe_cols = ['MultipleLines', 'InternetService', 'OnlineSecurity',
            'OnlineBackup', 'DeviceProtection', 'TechSupport',
            'StreamingTV', 'StreamingMovies', 'PaymentMethod']
df = pd.get_dummies(df, columns=ohe_cols, drop_first=True)
print(f"  ✅ One-Hot Encoding appliqué : {ohe_cols}")

print(f"\n  📐 Dataset après encodage : {df.shape[0]} lignes, {df.shape[1]} colonnes")


# ── 5. SÉPARATION FEATURES / CIBLE ───────────────────────────
print("\n── Séparation X / y ───────────────────────────────────")

X = df.drop(columns=['Churn'])
y = df['Churn']

print(f"  X (features) : {X.shape}")
print(f"  y (cible)    : {y.shape}")
print(f"  Distribution : {y.value_counts().to_dict()}")


# ── 6. SPLIT TRAIN / VALIDATION / TEST ───────────────────────
print("\n── Split Train / Val / Test ───────────────────────────")

# 70% train, 15% val, 15% test
X_temp, X_test, y_temp, y_test = train_test_split(
    X, y, test_size=0.15, random_state=42, stratify=y
)
X_train, X_val, y_train, y_val = train_test_split(
    X_temp, y_temp, test_size=0.176, random_state=42, stratify=y_temp
)

print(f"  Train      : {X_train.shape[0]} clients")
print(f"  Validation : {X_val.shape[0]} clients")
print(f"  Test       : {X_test.shape[0]} clients")
print(f"  Churn dans train    : {y_train.mean()*100:.1f}%")
print(f"  Churn dans val      : {y_val.mean()*100:.1f}%")
print(f"  Churn dans test     : {y_test.mean()*100:.1f}%")


# ── 7. NORMALISATION ─────────────────────────────────────────
print("\n── Normalisation (StandardScaler) ─────────────────────")

num_cols = ['tenure', 'MonthlyCharges', 'TotalCharges',
            'charges_per_tenure', 'nb_services']

scaler = StandardScaler()
X_train[num_cols] = scaler.fit_transform(X_train[num_cols])
X_val[num_cols]   = scaler.transform(X_val[num_cols])
X_test[num_cols]  = scaler.transform(X_test[num_cols])

print(f"  ✅ StandardScaler appliqué sur : {num_cols}")


# ── 8. SMOTE — RÉÉQUILIBRAGE DES CLASSES ─────────────────────
print("\n── SMOTE — Rééquilibrage ───────────────────────────────")
print(f"  Avant SMOTE — Churn: {y_train.sum()} | Non-Churn: {(y_train==0).sum()}")

smote = SMOTE(random_state=42)
X_train_sm, y_train_sm = smote.fit_resample(X_train, y_train)

print(f"  Après SMOTE — Churn: {y_train_sm.sum()} | Non-Churn: {(y_train_sm==0).sum()}")
print(f"  ✅ Dataset d'entraînement équilibré : {X_train_sm.shape[0]} échantillons")


# ── 9. SAUVEGARDE ─────────────────────────────────────────────
print("\n── Sauvegarde ─────────────────────────────────────────")

joblib.dump(X_train_sm, 'data_X_train.pkl')
joblib.dump(y_train_sm, 'data_y_train.pkl')
joblib.dump(X_val,      'data_X_val.pkl')
joblib.dump(y_val,      'data_y_val.pkl')
joblib.dump(X_test,     'data_X_test.pkl')
joblib.dump(y_test,     'data_y_test.pkl')
joblib.dump(scaler,     'scaler.pkl')

# Sauvegarder la liste des colonnes pour l'API
feature_names = list(X.columns)
joblib.dump(feature_names, 'feature_names.pkl')

print(f"""
  ✅ Fichiers sauvegardés :
     → data_X_train.pkl  ({X_train_sm.shape[0]} échantillons)
     → data_X_val.pkl    ({X_val.shape[0]} échantillons)
     → data_X_test.pkl   ({X_test.shape[0]} échantillons)
     → scaler.pkl
     → feature_names.pkl ({len(feature_names)} features)
""")

print("=" * 60)
print("  ✅ PREPROCESSING TERMINÉ — lancer 03_model.py")
print("=" * 60)