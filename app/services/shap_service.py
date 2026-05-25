import numpy as np
import shap


def explain_prediction(model, features, original_client: dict, top_n: int = 5) -> list[dict]:
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(features)
    if isinstance(shap_values, list):
        values = shap_values[1][0]
    else:
        values = shap_values[0]

    feature_names = list(features.columns)
    ranked = sorted(zip(feature_names, values), key=lambda item: abs(item[1]), reverse=True)[:top_n]
    reasons = []
    for feature, impact in ranked:
        reasons.append(
            {
                "feature": feature,
                "impact": float(np.round(impact, 6)),
                "valeur": original_client.get(feature),
            }
        )
    return reasons
