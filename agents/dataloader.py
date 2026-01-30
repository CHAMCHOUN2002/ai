import pandas as pd
import os
import numpy as np

class OULADDataLoader:
    def __init__(self, data_path="../data/oulad/"):
        self.data_path = data_path
        self.student_info = None
        self.student_assessment = None
        self.student_vle = None
        self.assessments = None
        self.courses = None

    def load_all(self):
        """Charge tous les fichiers OULAD et nettoie les NaN"""
        # Chargement des fichiers
        self.student_info = pd.read_csv(os.path.join(self.data_path, "studentInfo.csv"))
        self.student_assessment = pd.read_csv(os.path.join(self.data_path, "studentAssessment.csv"))
        self.student_vle = pd.read_csv(os.path.join(self.data_path, "studentVle.csv"))
        self.assessments = pd.read_csv(os.path.join(self.data_path, "assessments.csv"))
        self.courses = pd.read_csv(os.path.join(self.data_path, "courses.csv"))

        # ─── Nettoyage des NaN ───
        # Scores
        self.student_assessment["score"] = pd.to_numeric(self.student_assessment["score"], errors="coerce")
        self.student_assessment["score"] = self.student_assessment["score"].fillna(50.0)

        # Dates soumises manquantes → 0
        self.student_assessment["date_submitted"] = self.student_assessment["date_submitted"].fillna(0)

        # Total clicks manquants
        if "sum_click" in self.student_vle.columns:
            self.student_vle["sum_click"] = pd.to_numeric(self.student_vle["sum_click"], errors="coerce")
            self.student_vle["sum_click"] = self.student_vle["sum_click"].fillna(0.0)

        # Remplissage autres champs si nécessaire
        self.student_info["highest_education"] = self.student_info["highest_education"].fillna("Other")

        print("✅ All OULAD datasets loaded and cleaned successfully")

        return {
            "student_info": self.student_info,
            "student_assessment": self.student_assessment,
            "student_vle": self.student_vle,
            "assessments": self.assessments,
            "courses": self.courses
        }
