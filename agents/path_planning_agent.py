# path_planning_agent.py
# Path Planning Agent – Planifie le parcours pédagogique personnalisé
# Technologies : Graph search (A*) + heuristiques personnalisées
# Entrée : dict profil depuis Profiling Agent
# Sortie : liste de modules + assessments recommandés (chemin optimal basé sur données OULAD)

import networkx as nx
import pandas as pd
from heapq import heappush, heappop
from utils.visualize_graph import save_graph_image, save_path_image

class PathPlanningAgent:
    def __init__(self, data):
        """
        data = dictionnaire avec toutes les DataFrames OULAD :
        - courses, assessments, student_assessment, student_vle
        """
        self.courses = data["courses"]
        self.assessments = data["assessments"]
        self.student_assessment = data["student_assessment"]
        self.student_vle = data["student_vle"]

    def _build_graph(self, start_module=None):
        """ Construit le graphe pédagogique pour un profil donné """
        G = nx.DiGraph()

        # Modules triés alphabétiquement (proxy pour progression)
        modules_ordered = sorted(self.courses["code_module"].unique().tolist())

        # Nœuds modules
        for module in modules_ordered:
            row = self.courses[self.courses["code_module"] == module].iloc[0]
            length = row.get("module_presentation_length", 200)
            difficulty = min(5.0, max(1.0, length / 50.0)) if pd.notna(length) else 3.0
            G.add_node(module, type="module", difficulty=difficulty, code_module=module)

        # Nœuds assessments
        ass_sorted = self.assessments.sort_values(["code_module", "date", "id_assessment"])
        for _, row in ass_sorted.iterrows():
            module = row["code_module"]
            ass_id = row["id_assessment"]
            ass_type = row["assessment_type"]
            node_name = f"{module}_ass_{ass_id}"
            diff = 2.0 if ass_type == "CMA" else 4.0 if ass_type in ["TMA", "Exam"] else 3.5
            G.add_node(node_name, type="assessment", difficulty=diff, code_module=module)
            if module in G:
                G.add_edge(module, node_name, weight=diff * 0.6)

        # Progression module → module suivant
        for i in range(len(modules_ordered) - 1):
            current = modules_ordered[i]
            next_mod = modules_ordered[i + 1]
            ass_current = [n for n in G.nodes if n.startswith(current + "_ass_")]
            if ass_current:
                last_ass = sorted(ass_current, key=lambda x: int(x.split('_')[-1]))[-1]
                G.add_edge(last_ass, next_mod, weight=2.0)
            else:
                G.add_edge(current, next_mod, weight=2.5)

        # Start / End
        G.add_node("Start", type="start")
        G.add_node("End", type="end")

        # Start → start_module si défini, sinon premiers modules alphabétiques
        if start_module and start_module in G:
            G.add_edge("Start", start_module, weight=0.5)
        else:
            for mod in modules_ordered[:3]:
                G.add_edge("Start", mod, weight=0.5)

        # End : connecter dernier module et ses assessments
        last_mod = modules_ordered[-1]
        G.add_edge(last_mod, "End", weight=1.5)
        last_ass_nodes = [n for n in G.nodes if n.startswith(last_mod + "_ass_")]
        for ass in last_ass_nodes:
            G.add_edge(ass, "End", weight=1.0)

        print(f"Graphe construit : {G.number_of_nodes()} nœuds, {G.number_of_edges()} arêtes")
        return G

    def _heuristic(self, node, goal, profile, graph):
        """ Heuristique personnalisée pour le profil étudiant """
        if not nx.has_path(graph, node, goal):
            return 999.0

        base = nx.shortest_path_length(graph, node, goal, weight="weight")
        node_data = graph.nodes.get(node, {})
        n_type = node_data.get("type", "module")
        n_diff = node_data.get("difficulty", 3.0)

        style = profile.get("learning_style", "practice")
        risk = profile.get("risk_level", "medium")

        # Style learning influence le coût des assessments
        if n_type == "assessment":
            if style == "visual":
                base += 5.0
            elif style == "text":
                base += 3.0
            elif style == "practice":
                base -= 3.0

        # Adaptation risque
        if risk == "high" and n_diff > 3.0:
            base += 5.0
        elif risk == "low" and n_diff > 2.0:
            base -= 1.5

        return base

    def _a_star_search(self, start, goal, profile, graph):
        """ Recherche A* personnalisée """
        open_set = []
        heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self._heuristic(start, goal, profile, graph)}

        while open_set:
            _, current = heappop(open_set)

            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return path[::-1]

            for neighbor in graph.neighbors(current):
                tentative_g = g_score[current] + graph[current][neighbor]["weight"]
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f = tentative_g + self._heuristic(neighbor, goal, profile, graph)
                    f_score[neighbor] = f
                    heappush(open_set, (f, neighbor))

        return []  # Pas de chemin trouvé

    def plan_path(self, profile):
        """ Planifie le parcours pédagogique pour un profil donné """
        start_module = None
        student_id = profile.get("student_id")

        # Étudiant existant : chercher start_module depuis assessments ou VLE
        if student_id and profile["student_type"] == "existing":
            ass_student = self.student_assessment[self.student_assessment["id_student"] == student_id]
            if not ass_student.empty:
                ass_student = ass_student.copy()
                ass_student["date_submitted"] = pd.to_numeric(ass_student["date_submitted"], errors="coerce")
                merged = ass_student.merge(
                    self.assessments[["id_assessment", "code_module"]],
                    on="id_assessment",
                    how="left"
                )
                if not merged.empty:
                    recent_ass = merged.sort_values("date_submitted").dropna(subset=["code_module"]).iloc[-1]
                    start_module = recent_ass["code_module"]

            # Si pas d'assessment, utiliser VLE
            if start_module is None:
                vle_student = self.student_vle[self.student_vle["id_student"] == student_id]
                if not vle_student.empty:
                    vle_student = vle_student.copy()
                    vle_student["date"] = pd.to_numeric(vle_student["date"], errors="coerce")
                    recent_vle = vle_student.sort_values("date").iloc[-1]
                    start_module = recent_vle["code_module"]

        # Étudiant nouveau : utiliser preferred_module
        elif profile["student_type"] == "new":
            start_module = profile.get("preferred_module")

        # Rebuild graph spécifique pour ce profil
        graph = self._build_graph(start_module=start_module)

        # Calcul A*
        path = self._a_star_search("Start", "End", profile, graph)
        clean_path = [n for n in path if n not in ["Start", "End"]]

        notes = "Chemin planifié via A* avec données OULAD réelles (ordre chronologique + assessments)"
        if len(clean_path) < 3:
            notes += " (chemin court : historique étudiant limité ou peu d'assessments)"

        if clean_path:
            save_path_image(graph, clean_path)
        else:
            print("Pas de chemin valide → pas d'image générée")

        return {
            "planned_path": clean_path,
            "path_length": len(clean_path),
            "start_module_used": start_module if start_module else "fallback",
            "adapted_to_style": profile.get("learning_style"),
            "adapted_to_risk": profile.get("risk_level"),
            "notes": notes
        }
