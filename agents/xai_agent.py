class XAIAgent:
    def __init__(self, profiling_agent):
        self.profiling_agent = profiling_agent

    def explain(self, profile, planned_path, recommendation_results):
        style = profile.get("learning_style", "practice")
        risk = profile.get("risk_level", "medium")
        mean_score = profile.get("mean_score", 50.0)
        cluster_id = profile.get("cluster_id")

        explanations = {}

        # Profil
        feature_importance = {
            "mean_score": f"Votre score moyen élevé ({mean_score}) montre une bonne maîtrise – on peut vous proposer des étapes ambitieuses.",
            "learning_style": f"Votre style '{style}' nous pousse à privilégier les quizzes et exercices pratiques.",
            "risk_level": f"Risque '{risk}' → vous pouvez avancer sans trop de contraintes.",
            "total_clicks": f"Votre activité ({profile.get('total_clicks', 'inconnue')}) indique une bonne régularité."
        }
        explanations["feature_importance"] = feature_importance
        explanations["profil_summary"] = f"Vous êtes classé dans le cluster {cluster_id} : étudiants performants, réguliers et orientés pratique."

        # Chaîne globale
        chain = [
            "On commence par un parcours logique basé sur les données réelles (de BBB à GGG).",
            f"Votre style '{style}' favorise fortement les quizzes interactifs et les TMA.",
            f"Comme votre risque est '{risk}' et votre score élevé, on priorise les premiers modules sans pénalité.",
            "Les quizzes générés spécialement pour vous sont très adaptés → ils apparaissent souvent en priorité."
        ]

        # Contrefactuels (simples et utiles)
        counterfactuals = [
            f"Si ton risque était élevé (par exemple si tu avais moins de temps ou plus de difficulté), je te proposerais d’abord des quizzes très courts et faciles pour reprendre confiance.",
            f"Si tu préférais apprendre par la lecture plutôt que par la pratique, je mettrais en avant des textes détaillés et des explications longues au lieu des quizzes interactifs.",
            f"Si ton score moyen était plus bas (moins de 60), je commencerais par beaucoup plus de petits quizzes de révision pour t’aider à remonter ton niveau avant de passer aux modules difficiles."
        ]

        explanations["global_reasoning"] = {
            "chain": chain,
            "counterfactuals": counterfactuals
        }

        return {
            "explanations": explanations,
            "method": "Explications globales du système"
        }