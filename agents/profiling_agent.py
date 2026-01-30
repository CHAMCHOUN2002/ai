# profiling_agent.py
# Profiling Agent – Analyse profil & style d’apprentissage
# Entrée : dict depuis Interface Agent
# Sortie : profil structuré (cluster, score, risque)

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans


class ProfilingAgent:

    def __init__(self, data, n_clusters=3):
        """
        data = {
            "student_info": DataFrame,
            "student_assessment": DataFrame,
            "student_vle": DataFrame
        }
        """
        self.student_info = data["student_info"]
        self.student_assessment = data["student_assessment"]
        self.student_vle = data["student_vle"]

        self.n_clusters = n_clusters

        self.learning_style_mapping = {
            "visual": 0,
            "text": 1,
            "practice": 2
        }

        self.scaler = StandardScaler()
        self.kmeans = None

        self._fit_clusters()


    # --------------------------------------------------
    # Création embedding étudiant EXISTANT
    # --------------------------------------------------
    def _create_embedding_existing(self, student_id):
        student_id = int(student_id)

        if student_id not in self.student_info["id_student"].values:
            return None

        # Scores (chaine -> numerique)
        scores = pd.to_numeric(
            self.student_assessment[self.student_assessment["id_student"] == student_id]["score"],
            errors="coerce"
        )
        mean_score = scores.mean() if scores.notna().any() else 50.0
        score_std = scores.std() if scores.notna().any() else 10.0
        if np.isnan(score_std):
            score_std = 10.0  # valeur par défaut si NaN

        # Activité VLE
        clicks_df = self.student_vle[self.student_vle["id_student"] == student_id]
        total_clicks = clicks_df["sum_click"].sum() if not clicks_df.empty else 0.0
        clicks_per_day = total_clicks / (len(clicks_df) if len(clicks_df) > 0 else 1)
        if np.isnan(clicks_per_day):
            clicks_per_day = 0.0

        # Modules complétés
        completed_modules = self.student_assessment[
            (self.student_assessment["id_student"] == student_id) & 
            (pd.to_numeric(self.student_assessment["score"], errors="coerce") >= 50)
        ]["id_assessment"].nunique()

        # Style apprentissage
        edu = self.student_info[self.student_info["id_student"] == student_id]["highest_education"].iloc[0]
        if edu in ["HE qualification", "Postgraduate"]:
            style = "text"
        elif edu in ["A Level", "Lower Than A Level"]:
            style = "visual"
        else:
            style = "practice"
        style_num = self.learning_style_mapping[style]

        # Nettoyage final de l'embedding pour KMeans
        embedding = [mean_score, score_std, total_clicks, clicks_per_day, style_num, completed_modules]
        embedding = [0.0 if np.isnan(x) else x for x in embedding]  # sécurité NaN

        return embedding

    # --------------------------------------------------
    # Entraînement KMeans
    # --------------------------------------------------
    def _fit_clusters(self):
        print("→ Entraînement du Profiling Agent...")

        student_ids = self.student_info["id_student"].unique()  # ajustable

        embeddings = []
        for sid in student_ids:
            emb = self._create_embedding_existing(sid)
            if emb is not None:
                embeddings.append(emb)

        X = np.array(embeddings)
        X_scaled = self.scaler.fit_transform(X)

        self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        self.kmeans.fit(X_scaled)

        print(f"→ Clustering terminé ({self.n_clusters} clusters)")


    # --------------------------------------------------
    # API principale appelée par l’Interface Agent
    # --------------------------------------------------
    def profile_student(self, input_json):

        student_type = input_json.get("student_type")

        # ================= EXISTING STUDENT =================
        if student_type == "existing":
            student_id = input_json.get("student_id")

            emb = self._create_embedding_existing(student_id)

            if emb is None:
                return {
                    "error": "STUDENT_NOT_FOUND",
                    "message": f"L'étudiant {student_id} n'existe pas dans la base."
                }

            emb_scaled = self.scaler.transform([emb])
            cluster = int(self.kmeans.predict(emb_scaled)[0])

            mean_score = round(emb[0], 1)
            risk = "high" if mean_score < 60 else "medium" if mean_score < 80 else "low"

            return {
                "student_type": "existing",
                "student_id": int(student_id),
                "mean_score": mean_score,
                "total_clicks": int(emb[2]),
                "learning_style": list(self.learning_style_mapping.keys())[emb[4]],
                "cluster_id": cluster,
                "risk_level": risk
            }

        # ================= NEW STUDENT =================
        elif student_type == "new":
            level = input_json.get("level", "beginner")

            score_map = {
                "beginner": 50.0,
                "intermediate": 70.0,
                "advanced": 85.0
            }

            est_score = score_map.get(level, 50.0)

            style = input_json.get("learning_style", "practice")
            style_num = self.learning_style_mapping.get(style, 2)

            emb = [est_score, 0.0, 0.0, 0.0, style_num, 0]  # estimé
            emb_scaled = self.scaler.transform([emb])
            cluster = int(self.kmeans.predict(emb_scaled)[0])

            return {
                "student_type": "new",
                "level": level,
                "preferred_module": input_json.get("preferred_module"),
                "learning_style": style,
                "estimated_score": est_score,
                "cluster_id": cluster
            }

        # ================= ERREUR =================
        return {"error": "student_type invalide"}
