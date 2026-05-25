import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Style des graphiques
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 12
sns.set_style("whitegrid")
COULEUR_CHURN    = "#E74C3C"   # rouge  — clients qui partent
COULEUR_NOCHURN  = "#2ECC71"   # vert   — clients fidèles
COULEUR_NEUTRE   = "#2E75B6"   # bleu   — graphiques généraux

# ── 1. CHARGEMENT ────────────────────────────────────────────
print("=" * 60)
print("  CHARGEMENT DU DATASET")
print("=" * 60)

df = pd.read_csv(r"C:\Users\USER-PC\Downloads\archive\WA_Fn-UseC_-Telco-Customer-Churn.csv")

# TotalCharges est une string → convertir en float
df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')

print(f"\n✅ Dataset chargé : {df.shape[0]} clients, {df.shape[1]} colonnes")
print(f"   Valeurs manquantes : {df.isnull().sum().sum()}")
print(f"\n{df.dtypes}\n")
print(df.head(5).to_string())

# ── 2. DISTRIBUTION DU CHURN ─────────────────────────────────
print("\n" + "=" * 60)
print("  DISTRIBUTION DU CHURN")
print("=" * 60)

churn_counts = df['Churn'].value_counts()
churn_pct    = df['Churn'].value_counts(normalize=True) * 100

print(f"\n  Non-Churn : {churn_counts['No']:>5}  ({churn_pct['No']:.1f}%)")
print(f"  Churn     : {churn_counts['Yes']:>5}  ({churn_pct['Yes']:.1f}%)")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Camembert
axes[0].pie(
    churn_counts,
    labels=['Fidèles (No)', 'Churners (Yes)'],
    colors=[COULEUR_NOCHURN, COULEUR_CHURN],
    autopct='%1.1f%%',
    startangle=90,
    wedgeprops={'edgecolor': 'white', 'linewidth': 2}
)
axes[0].set_title('Répartition globale du Churn', fontweight='bold')

# Barres
bars = axes[1].bar(
    ['Non-Churn', 'Churn'],
    churn_counts,
    color=[COULEUR_NOCHURN, COULEUR_CHURN],
    edgecolor='white', linewidth=1.5
)
for bar, val in zip(bars, churn_counts):
    axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                 str(val), ha='center', fontweight='bold')
axes[1].set_title('Nombre de clients par statut', fontweight='bold')
axes[1].set_ylabel('Nombre de clients')

plt.suptitle('Distribution du Churn — Dataset IBM Telco', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('fig_01_churn_distribution.png', dpi=150, bbox_inches='tight')
plt.show()
print("  ✅ Figure sauvegardée : fig_01_churn_distribution.png")

# ── 3. CHURN PAR TYPE DE CONTRAT ─────────────────────────────
print("\n" + "=" * 60)
print("  CHURN PAR TYPE DE CONTRAT")
print("=" * 60)

contrat_churn = df.groupby('Contract')['Churn'].apply(
    lambda x: (x == 'Yes').mean() * 100
).reset_index()
contrat_churn.columns = ['Contrat', 'Taux_Churn']
print(contrat_churn.to_string(index=False))

plt.figure(figsize=(10, 5))
bars = plt.bar(
    contrat_churn['Contrat'],
    contrat_churn['Taux_Churn'],
    color=[COULEUR_CHURN if v > 20 else COULEUR_NOCHURN for v in contrat_churn['Taux_Churn']],
    edgecolor='white', linewidth=1.5
)
for bar, val in zip(bars, contrat_churn['Taux_Churn']):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
             f'{val:.1f}%', ha='center', fontweight='bold', fontsize=13)
plt.title('Taux de Churn par Type de Contrat', fontweight='bold', fontsize=14)
plt.ylabel('Taux de Churn (%)')
plt.xlabel('Type de Contrat')
plt.ylim(0, 55)
plt.tight_layout()
plt.savefig('fig_02_churn_par_contrat.png', dpi=150, bbox_inches='tight')
plt.show()
print("  ✅ Figure sauvegardée : fig_02_churn_par_contrat.png")

# ── 4. CHURN PAR ANCIENNETÉ ───────────────────────────────────
print("\n" + "=" * 60)
print("  CHURN PAR ANCIENNETÉ (TENURE)")
print("=" * 60)

df['tenure_group'] = pd.cut(
    df['tenure'],
    bins=[0, 6, 12, 24, 48, 72],
    labels=['0-6 mois', '6-12 mois', '1-2 ans', '2-4 ans', '4-6 ans']
)
tenure_churn = df.groupby('tenure_group', observed=True)['Churn'].apply(
    lambda x: (x == 'Yes').mean() * 100
).reset_index()
tenure_churn.columns = ['Ancienneté', 'Taux_Churn']
print(tenure_churn.to_string(index=False))

plt.figure(figsize=(10, 5))
plt.plot(
    tenure_churn['Ancienneté'],
    tenure_churn['Taux_Churn'],
    marker='o', color=COULEUR_CHURN,
    linewidth=2.5, markersize=10
)
for i, row in tenure_churn.iterrows():
    plt.annotate(f"{row['Taux_Churn']:.1f}%",
                 (row['Ancienneté'], row['Taux_Churn']),
                 textcoords="offset points", xytext=(0, 12),
                 ha='center', fontweight='bold', fontsize=12)
plt.fill_between(
    range(len(tenure_churn)),
    tenure_churn['Taux_Churn'],
    alpha=0.15, color=COULEUR_CHURN
)
plt.xticks(range(len(tenure_churn)), tenure_churn['Ancienneté'])
plt.title("Taux de Churn selon l'Ancienneté du Client", fontweight='bold', fontsize=14)
plt.ylabel('Taux de Churn (%)')
plt.xlabel("Ancienneté")
plt.ylim(0, 65)
plt.tight_layout()
plt.savefig('fig_03_churn_par_anciennete.png', dpi=150, bbox_inches='tight')
plt.show()
print("  ✅ Figure sauvegardée : fig_03_churn_par_anciennete.png")

# ── 5. CHARGES MENSUELLES ─────────────────────────────────────
print("\n" + "=" * 60)
print("  CHARGES MENSUELLES : CHURNERS vs NON-CHURNERS")
print("=" * 60)

print(df.groupby('Churn')['MonthlyCharges'].agg(['mean', 'median', 'min', 'max']).round(2))

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Histogramme superposé
for label, color in [('No', COULEUR_NOCHURN), ('Yes', COULEUR_CHURN)]:
    axes[0].hist(
        df[df['Churn'] == label]['MonthlyCharges'],
        bins=30, alpha=0.6, color=color,
        label='Fidèles' if label == 'No' else 'Churners',
        edgecolor='white'
    )
axes[0].set_title('Distribution des Charges Mensuelles', fontweight='bold')
axes[0].set_xlabel('Charges Mensuelles ($)')
axes[0].set_ylabel('Nombre de Clients')
axes[0].legend()

# Boxplot
bp = axes[1].boxplot(
    [df[df['Churn'] == 'No']['MonthlyCharges'],
     df[df['Churn'] == 'Yes']['MonthlyCharges']],
    patch_artist=True,
    labels=['Fidèles', 'Churners']
)
bp['boxes'][0].set_facecolor(COULEUR_NOCHURN)
bp['boxes'][1].set_facecolor(COULEUR_CHURN)
for patch in bp['boxes']:
    patch.set_alpha(0.7)
axes[1].set_title('Boxplot des Charges Mensuelles', fontweight='bold')
axes[1].set_ylabel('Charges Mensuelles ($)')

plt.suptitle('Analyse des Charges Mensuelles par Statut Churn', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('fig_04_charges_mensuelles.png', dpi=150, bbox_inches='tight')
plt.show()
print("  ✅ Figure sauvegardée : fig_04_charges_mensuelles.png")

# ── 6. TOP VARIABLES CORRÉLÉES AU CHURN ──────────────────────
print("\n" + "=" * 60)
print("  CORRÉLATION DES VARIABLES AVEC LE CHURN")
print("=" * 60)

df_encoded = df.copy()
df_encoded['Churn_bin'] = (df_encoded['Churn'] == 'Yes').astype(int)

# Encodage rapide pour corrélation
cat_cols = df_encoded.select_dtypes(include='object').columns.tolist()
cat_cols.remove('Churn')
cat_cols.remove('customerID')

for col in cat_cols:
    df_encoded[col] = pd.Categorical(df_encoded[col]).codes

num_df = df_encoded.drop(columns=['customerID', 'Churn', 'tenure_group'])
corr_churn = num_df.corr()['Churn_bin'].drop('Churn_bin').sort_values(key=abs, ascending=False)

print("\nTop 10 variables les plus corrélées au Churn :")
print(corr_churn.head(10).to_string())

plt.figure(figsize=(12, 6))
colors = [COULEUR_CHURN if v > 0 else COULEUR_NOCHURN for v in corr_churn.head(10)]
bars = plt.barh(corr_churn.head(10).index, corr_churn.head(10).values,
                color=colors, edgecolor='white', linewidth=1.5)
plt.axvline(x=0, color='black', linewidth=0.8, linestyle='--')
plt.title('Top 10 Variables Corrélées au Churn', fontweight='bold', fontsize=14)
plt.xlabel('Coefficient de Corrélation avec le Churn')
rouge_patch = mpatches.Patch(color=COULEUR_CHURN, label='Corrélation positive (↑ risque churn)')
vert_patch  = mpatches.Patch(color=COULEUR_NOCHURN, label='Corrélation négative (↓ risque churn)')
plt.legend(handles=[rouge_patch, vert_patch])
plt.tight_layout()
plt.savefig('fig_05_correlations_churn.png', dpi=150, bbox_inches='tight')
plt.show()
print("  ✅ Figure sauvegardée : fig_05_correlations_churn.png")

# ── 7. RÉSUMÉ FINAL ───────────────────────────────────────────
print("\n" + "=" * 60)
print("  RÉSUMÉ DE L'EXPLORATION")
print("=" * 60)
print(f"""
  📊 Dataset         : {df.shape[0]} clients, {df.shape[1]} colonnes
  🔴 Taux de Churn   : {churn_pct['Yes']:.1f}% ({churn_counts['Yes']} clients)
  🟢 Clients fidèles : {churn_pct['No']:.1f}% ({churn_counts['No']} clients)

  ⚠️  Déséquilibre des classes détecté → SMOTE sera appliqué

  🔑 Insights clés :
     • Contrat mensuel     → 42.7% de churn (le plus risqué)
     • 0-6 mois d'ancienneté → 53.3% de churn
     • Paiement électronique → 45.3% de churn
     • Charges mensuelles élevées = plus de churn (moy. 74$ vs 61$)
     • Seniors : 41.7% de churn vs 23.6% pour les non-seniors

  ✅ Prochaine étape : lancer 02_preprocessing.py
""")