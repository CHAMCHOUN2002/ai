# utils/visualize_graph.py
import os
import matplotlib.pyplot as plt
import networkx as nx

def save_graph_image(graph, filename="static/graphe_pedagogique.png", title="Graphe pédagogique"):
    """
    Sauvegarde une image PNG du graphe dans le dossier static/
    """
    try:
        plt.figure(figsize=(16, 12))
        
        # Layout adapté (kamada_kawai ou spring pour graphes moyens)
        pos = nx.kamada_kawai_layout(graph) if len(graph) < 300 else nx.spring_layout(graph, seed=42)
        
        # Couleurs par type de nœud
        node_colors = []
        for node, data in graph.nodes(data=True):
            n_type = data.get('type', 'unknown')
            if n_type == 'module':
                node_colors.append('lightblue')
            elif n_type == 'assessment':
                node_colors.append('lightgreen')
            elif n_type == 'start':
                node_colors.append('orange')
            elif n_type == 'end':
                node_colors.append('red')
            else:
                node_colors.append('gray')

        nx.draw(graph, pos, with_labels=False, node_color=node_colors,
                node_size=500, arrows=True, edge_color='gray', width=0.8,
                arrowstyle='->', arrowsize=15)
        
        plt.title(title)
        plt.axis('off')
        
        # Créer dossier static si absent
        os.makedirs("static", exist_ok=True)
        full_path = os.path.join(os.getcwd(), filename)
        plt.savefig(full_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"Image sauvegardée : {full_path}")
        return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde de l'image : {e}")
        return False


def save_path_image(graph, planned_path, filename="static/chemin_recommande.png"):
    """
    Sauvegarde uniquement le chemin recommandé (plus lisible)
    """
    try:
        path_graph = nx.DiGraph()
        full_path = ['Start'] + planned_path + ['End']
        for i in range(len(full_path)-1):
            path_graph.add_edge(full_path[i], full_path[i+1])
        
        pos = nx.circular_layout(path_graph)  # ou nx.spring_layout pour plus de clarté
        
        plt.figure(figsize=(10, 6))
        nx.draw(path_graph, pos, with_labels=True, node_color='lightgreen',
                node_size=1500, font_size=10, font_weight='bold',
                arrows=True, arrowstyle='->', arrowsize=20)
        
        plt.title("Parcours recommandé pour l'étudiant")
        plt.axis('off')
        
        os.makedirs("static", exist_ok=True)
        full_path_img = os.path.join(os.getcwd(), filename)
        plt.savefig(full_path_img, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"Image du chemin sauvegardée : {full_path_img}")
        return True
    except Exception as e:
        print(f"Erreur chemin viz: {e}")
        return False