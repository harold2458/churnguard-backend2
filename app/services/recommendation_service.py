def generate_recommendations(client: dict, behavior: dict | None = None) -> list[str]:
    recommendations: list[str] = []
    behavior = behavior or {}

    if client.get("Contract") == "Month-to-month":
        recommendations.append("Proposer un contrat annuel avec une réduction de fidélité.")
    if float(client.get("MonthlyCharges") or 0) >= 80:
        recommendations.append("Proposer une offre tarifaire mieux adaptée au profil de consommation.")
    if int(client.get("tenure") or 0) <= 6:
        recommendations.append("Mettre en place un suivi personnalisé pour nouveau client.")
    if client.get("TechSupport") in {"No", "No internet service"}:
        recommendations.append("Offrir une assistance technique gratuite ou un diagnostic de service.")
    if int(behavior.get("nombre_reclamations") or 0) >= 3:
        recommendations.append("Prioriser un appel commercial pour résoudre les réclamations.")
    if int(behavior.get("retards_paiement") or 0) >= 2:
        recommendations.append("Proposer un accompagnement de paiement ou un rappel personnalisé.")

    if not recommendations:
        recommendations.append("Maintenir la relation client avec une offre de fidélisation légère.")
    return recommendations
