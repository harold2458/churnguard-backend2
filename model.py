# ============================================================
#  SYSTÈME ANTI-CHURN — ÉTAPE 3 : ENTRAÎNEMENT DU MODÈLE
#  Algorithme : XGBoost avec optimisation Optuna + SHAP
#  Auteur     : [Ton Nom]
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import joblib
import warnings
warnings.filterwarnings('ignore')

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report, confusion_matrix,
    roc_auc_score, roc_curve, precision_recall_curve,
    f1_score, precision_score, recall_score
)
import xgboost as xgb
import shap
import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)

plt.rcParams['figure.figsize'] = (12, 6)
sns.set_style("whitegrid")
COULEUR_CHURN   = "#E74C3C"
COULEUR_NOCHURN = "#2ECC71"
COULEUR_NEUTRE  = "#2E75B6"

print("=" * 60)
print("  ENTRAÎNEMENT DU MODÈLE ANTI-CHURN")
print("=" * 60)


# ── 1. CHARGEMENT DES DONNÉES ────────────────────────────────
X_train = joblib.load('data_X_train.pkl')
y_train = joblib.load('data_y_train.pkl')
X_val   = joblib.load('data_X_val.pkl')
y_val   = joblib.load('data_y_val.pkl')
X_test  = joblib.load('data_X_test.pkl')
y_test  = joblib.load('data_y_test.pkl')
feature_names = joblib.load('feature_names.pkl')

print(f"\n✅ Données chargées")
print(f"   Train : {X_train.shape}, Val : {X_val.shape}, Test : {X_test.shape}")


# ── 2. BASELINE — RÉGRESSION LOGISTIQUE ──────────────────────
print("\n── Baseline : Régression Logistique ───────────────────")

lr = LogisticRegression(max_iter=1000, random_state=42)
lr.fit(X_train, y_train)
y_pred_lr = lr.predict(X_val)
y_prob_lr = lr.predict_proba(X_val)[:, 1]
auc_lr    = roc_auc_score(y_val, y_prob_lr)
f1_lr     = f1_score(y_val, y_pred_lr)
print(f"  AUC-ROC : {auc_lr:.4f} | F1-Score : {f1_lr:.4f}")


# ── 3. RANDOM FOREST ─────────────────────────────────────────
print("\n── Random Forest ───────────────────────────────────────")

rf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)
y_pred_rf = rf.predict(X_val)
y_prob_rf = rf.predict_proba(X_val)[:, 1]
auc_rf    = roc_auc_score(y_val, y_prob_rf)
f1_rf     = f1_score(y_val, y_pred_rf)
print(f"  AUC-ROC : {auc_rf:.4f} | F1-Score : {f1_rf:.4f}")


# ── 4. XGBOOST OPTIMISÉ AVEC OPTUNA ─────────────────────────
print("\n── XGBoost + Optuna (optimisation bayésienne) ─────────")
print("   Recherche des meilleurs hyperparamètres...")

def objective(trial):
    params = {
        'n_estimators':       trial.suggest_int('n_estimators', 100, 500),
        'max_depth':          trial.suggest_int('max_depth', 3, 8),
        'learning_rate':      trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'subsample':          trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree':   trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'reg_alpha':          trial.suggest_float('reg_alpha', 1e-5, 10.0, log=True),
        'reg_lambda':         trial.suggest_float('reg_lambda', 1e-5, 10.0, log=True),
        'use_label_encoder':  False,
        'eval_metric':        'logloss',
        'random_state':       42,
        'n_jobs':             -1
    }
    model = xgb.XGBClassifier(**params)
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    y_prob = model.predict_proba(X_val)[:, 1]
    return roc_auc_score(y_val, y_prob)

study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=50, show_progress_bar=False)

best_params = study.best_params
best_params.update({
    'use_label_encoder': False,
    'eval_metric': 'logloss',
    'random_state': 42,
    'n_jobs': -1
})
print(f"  ✅ Meilleurs hyperparamètres trouvés :")
for k, v in best_params.items():
    if k not in ['use_label_encoder', 'eval_metric', 'random_state', 'n_jobs']:
        print(f"     {k:25s} = {v}")

# Entraînement final avec les meilleurs paramètres
xgb_model = xgb.XGBClassifier(**best_params)
xgb_model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    verbose=False
)

y_pred_xgb = xgb_model.predict(X_val)
y_prob_xgb = xgb_model.predict_proba(X_val)[:, 1]
auc_xgb    = roc_auc_score(y_val, y_prob_xgb)
f1_xgb     = f1_score(y_val, y_pred_xgb)
print(f"\n  AUC-ROC : {auc_xgb:.4f} | F1-Score : {f1_xgb:.4f}")


# ── 5. COMPARAISON DES MODÈLES ────────────────────────────────
print("\n── Comparaison des Modèles ─────────────────────────────")

resultats = {
    'Régression Logistique': {'AUC-ROC': auc_lr,  'F1-Score': f1_lr},
    'Random Forest':         {'AUC-ROC': auc_rf,  'F1-Score': f1_rf},
    'XGBoost (Optimisé)':   {'AUC-ROC': auc_xgb, 'F1-Score': f1_xgb},
}

df_res = pd.DataFrame(resultats).T
print(f"\n{df_res.round(4).to_string()}")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

modeles   = list(resultats.keys())
aucs      = [resultats[m]['AUC-ROC'] for m in modeles]
f1s       = [resultats[m]['F1-Score'] for m in modeles]
colors_bar = [COULEUR_NOCHURN, COULEUR_NEUTRE, COULEUR_CHURN]

for ax, vals, title, ylabel in [
    (axes[0], aucs, 'AUC-ROC par Modèle', 'AUC-ROC'),
    (axes[1], f1s,  'F1-Score par Modèle', 'F1-Score')
]:
    bars = ax.bar(modeles, vals, color=colors_bar, edgecolor='white', linewidth=1.5)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                f'{v:.4f}', ha='center', fontweight='bold', fontsize=11)
    ax.set_title(title, fontweight='bold', fontsize=13)
    ax.set_ylabel(ylabel)
    ax.set_ylim(0.5, 1.0)
    ax.tick_params(axis='x', rotation=15)

plt.suptitle('Comparaison des Modèles ML — Validation Set', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('fig_06_comparaison_modeles.png', dpi=150, bbox_inches='tight')
plt.show()
print("  ✅ Figure sauvegardée : fig_06_comparaison_modeles.png")


# ── 6. ÉVALUATION FINALE SUR LE JEU DE TEST ──────────────────
print("\n── Évaluation Finale sur le Jeu de TEST ───────────────")
print("   ⚠️  Ce jeu n'a jamais été vu par le modèle !")


y_prob_final = xgb_model.predict_proba(X_test)[:, 1]
seuil = 0.60
y_pred_final = (y_prob_final >= seuil).astype(int)

auc_final = roc_auc_score(y_test, y_prob_final)
f1_final  = f1_score(y_test, y_pred_final)
prec_final = precision_score(y_test, y_pred_final)
rec_final  = recall_score(y_test, y_pred_final)

print(f"""
  ┌─────────────────────────────────────┐
  │  RÉSULTATS FINAUX (Jeu de Test)     │
  ├─────────────────────────────────────┤
  │  AUC-ROC   : {auc_final:.4f}                  │
  │  F1-Score  : {f1_final:.4f}                  │
  │  Précision : {prec_final:.4f}                  │
  │  Rappel    : {rec_final:.4f}                  │
  └─────────────────────────────────────┘
""")
print(classification_report(y_test, y_pred_final,
                             target_names=['Fidèle', 'Churner']))


# ── 7. MATRICE DE CONFUSION ───────────────────────────────────
cm = confusion_matrix(y_test, y_pred_final)
plt.figure(figsize=(7, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='RdYlGn',
            xticklabels=['Fidèle', 'Churner'],
            yticklabels=['Fidèle', 'Churner'],
            linewidths=2, linecolor='white')
plt.title('Matrice de Confusion — XGBoost (Test Set)', fontweight='bold', fontsize=14)
plt.ylabel('Vraie Classe')
plt.xlabel('Classe Prédite')
plt.tight_layout()
plt.savefig('fig_07_matrice_confusion.png', dpi=150, bbox_inches='tight')
plt.show()
print("  ✅ Figure sauvegardée : fig_07_matrice_confusion.png")


# ── 8. COURBE ROC ────────────────────────────────────────────
plt.figure(figsize=(8, 6))
fpr, tpr, _ = roc_curve(y_test, y_prob_final)
plt.plot(fpr, tpr, color=COULEUR_CHURN, linewidth=2.5,
         label=f'XGBoost (AUC = {auc_final:.4f})')
plt.plot([0, 1], [0, 1], color='grey', linestyle='--', linewidth=1.5, label='Aléatoire')
plt.fill_between(fpr, tpr, alpha=0.15, color=COULEUR_CHURN)
plt.title('Courbe ROC — XGBoost Optimisé', fontweight='bold', fontsize=14)
plt.xlabel('Taux de Faux Positifs')
plt.ylabel('Taux de Vrais Positifs (Rappel)')
plt.legend(loc='lower right', fontsize=12)
plt.tight_layout()
plt.savefig('fig_08_courbe_roc.png', dpi=150, bbox_inches='tight')
plt.show()
print("  ✅ Figure sauvegardée : fig_08_courbe_roc.png")


# ── 9. SHAP — EXPLICABILITÉ ───────────────────────────────────
print("\n── SHAP — Explicabilité du Modèle ──────────────────────")

explainer   = shap.TreeExplainer(xgb_model)
shap_values = explainer.shap_values(X_test)

# Summary Plot — importance globale
plt.figure(figsize=(12, 8))
shap.summary_plot(shap_values, X_test,
                  feature_names=feature_names,
                  plot_type='bar',
                  show=False,
                  color=COULEUR_CHURN)
plt.title('SHAP — Importance Globale des Features', fontweight='bold', fontsize=14)
plt.tight_layout()
plt.savefig('fig_09_shap_importance.png', dpi=150, bbox_inches='tight')
plt.show()
print("  ✅ Figure sauvegardée : fig_09_shap_importance.png")

# Beeswarm Plot — distribution des impacts
plt.figure(figsize=(12, 8))
shap.summary_plot(shap_values, X_test,
                  feature_names=feature_names,
                  show=False)
plt.title('SHAP — Distribution des Impacts par Feature', fontweight='bold', fontsize=14)
plt.tight_layout()
plt.savefig('fig_10_shap_beeswarm.png', dpi=150, bbox_inches='tight')
plt.show()
print("  ✅ Figure sauvegardée : fig_10_shap_beeswarm.png")

# Exemple explication locale — 1 client churner
churners_idx = np.where(y_test == 1)[0]
idx_exemple  = churners_idx[0]

shap_client  = shap_values[idx_exemple]
top5_idx     = np.argsort(np.abs(shap_client))[-5:][::-1]
top5_features = [feature_names[i] for i in top5_idx]
top5_values  = shap_client[top5_idx]

print(f"\n  🔍 Explication locale — Client #{idx_exemple}")
print(f"  Score de churn prédit : {y_prob_final[idx_exemple]:.1%}")
print(f"\n  Top 5 raisons :")
for feat, val in zip(top5_features, top5_values):
    signe = "↑ risque" if val > 0 else "↓ risque"
    print(f"     {feat:30s} : {val:+.4f}  ({signe})")


# ── 10. SAUVEGARDE DU MODÈLE ──────────────────────────────────
print("\n── Sauvegarde du Modèle ───────────────────────────────")

joblib.dump(xgb_model,  'churn_model.pkl')
joblib.dump(explainer,  'shap_explainer.pkl')

# Sauvegarder les métriques
metriques = {
    'auc_roc':    float(auc_final),
    'f1_score':   float(f1_final),
    'precision':  float(prec_final),
    'recall':     float(rec_final)
}
joblib.dump(metriques, 'model_metrics.pkl')

print(f"""
  ✅ Fichiers sauvegardés :
     → churn_model.pkl
     → shap_explainer.pkl
     → model_metrics.pkl
""")

print("=" * 60)
print(f"  ✅ MODÈLE ENTRAÎNÉ — AUC-ROC : {auc_final:.4f}")
print("  ✅ Prochaine étape : lancer 04_api.py")
print("=" * 60)

# ── 11. AFFICHAGE FINAL DES MÉTRIQUES ────────────────────────
print("\n" + "=" * 60)
print("  📊 RÉCAPITULATIF FINAL DES MÉTRIQUES")
print("=" * 60)

metriques_affichage = {
    'AUC-ROC':   auc_final,
    'F1-Score':  f1_final,
    'Précision': prec_final,
    'Rappel':    rec_final,
}

fig, axes = plt.subplots(1, 4, figsize=(16, 4))

for ax, (nom, valeur) in zip(axes, metriques_affichage.items()):
    couleur = COULEUR_CHURN if valeur < 0.75 else COULEUR_NOCHURN if valeur >= 0.85 else COULEUR_NEUTRE
    ax.pie(
        [valeur, 1 - valeur],
        colors=[couleur, '#ECECEC'],
        startangle=90,
        counterclock=False,
        wedgeprops=dict(width=0.4)
    )
    ax.text(0, 0, f"{valeur:.1%}", ha='center', va='center',
            fontsize=18, fontweight='bold', color=couleur)
    ax.set_title(nom, fontweight='bold', fontsize=13)

plt.suptitle('Métriques Finales — XGBoost Optimisé (Test Set)',
             fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('fig_11_metriques_finales.png', dpi=150, bbox_inches='tight')
plt.show()
print("  ✅ Figure sauvegardée : fig_11_metriques_finales.png")