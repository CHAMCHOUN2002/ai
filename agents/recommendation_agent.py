class RecommendationAgent:
    def __init__(self, data):
        self.assessments = data["assessments"]

    def recommend(self, profile, planned_path, generated_content=None):
        style = profile.get("learning_style", "practice")
        risk = profile.get("risk_level", "medium")
        mean_score = profile.get("mean_score", 50.0)
        student_type = profile.get("student_type", "existing")

        recommendations = []

        # 1. Éléments du planned_path
        for idx, item in enumerate(planned_path):
            score = 68.0 + (idx * -1.5)

            item_str = str(item).lower()
            if "_ass_" in item_str:
                if "tma" in item_str and style == "practice":
                    score += 28
                elif "cma" in item_str and style in ["visual", "practice"]:
                    score += 24
                elif "exam" in item_str and style == "text":
                    score += 18
            else:
                if mean_score > 75:
                    score += 12

            if risk == "high" and any(kw in item_str for kw in ["exam", "tma"]):
                score -= 22
            elif risk == "low":
                score += 15

            if student_type == "existing" and mean_score > 60:
                score += 10

            # Explication user-friendly
            if "_ass_" not in item_str:
                expl = f"Commencez par le module {item} – parfait pour consolider vos bases avec des exercices concrets."
            else:
                expl = f"Testez-vous avec l'assessment {item} – un bon moyen de valider vos acquis en pratique."

            if mean_score > 80:
                expl += " Vous avez déjà un très bon niveau, on peut avancer rapidement ici."

            recommendations.append({
                "type": "planned_item",
                "item": item,
                "priority_score": round(score, 1),
                "explanation": expl
            })

        # 2. Quizzes réels
        if generated_content:
            quizzes = generated_content.get("quizzes_structured", [])

            for quiz in quizzes:
                q_score = 82.0
                if style == "practice":
                    q_score += 14
                if risk == "high":
                    q_score += 10

                q_text = quiz.get("question", "").lower()
                if any(word in q_text for word in ["explain", "difference", "why", "how"]):
                    q_score += 6

                # Explication user-friendly
                expl = f"Quiz rapide : « {quiz.get('question', 'Quiz généré')[:70]}... » – idéal pour tester vos connaissances en mode pratique."

                recommendations.append({
                    "type": "quiz_generated",
                    "number": quiz.get("number"),
                    "question": quiz.get("question", "Quiz sans titre"),
                    "answer_preview": quiz.get("answer", "")[:80] + "..." if quiz.get("answer") else "",
                    "priority_score": round(q_score, 1),
                    "explanation": expl
                })

        recommendations.sort(key=lambda x: x["priority_score"], reverse=True)
        top_recs = recommendations[:8]

        return {
            "recommended_next_steps": top_recs,
            "method": "Règles personnalisées basées sur votre style et votre niveau"
        }