from flask import Flask, render_template, request
from dataloader import OULADDataLoader
from profiling_agent import ProfilingAgent
from path_planning_agent import PathPlanningAgent
from content_generator_rag import ContentGeneratorRAG
from recommendation_agent import RecommendationAgent
from xai_agent import XAIAgent
app = Flask(__name__)

# ─── Chargement des données et initialisation des agents ───
loader = OULADDataLoader()
data = loader.load_all()
profiling_agent = ProfilingAgent(data)
path_planning_agent = PathPlanningAgent(data)
rec_agent = RecommendationAgent(data)

# ─── Content Generator  ───
content_llm = ContentGeneratorRAG()  #

# ─── Route principale ───
@app.route("/", methods=["GET", "POST"])
def interface():
    student_type = None
    profiling_result = None
    planning_result = None
    content_results = None
    rec_results = None
    xai_results = None

     # ─── XAI Agent ───
    if request.method == "POST":
        student_type = request.form.get("student_type")

        if student_type == "existing":
            profiling_result = profiling_agent.profile_student({
                "student_type": "existing",
                "student_id": request.form.get("student_id")
            })

        elif student_type == "new":
            profiling_result = profiling_agent.profile_student({
                "student_type": "new",
                "level": request.form.get("level"),
                "preferred_module": request.form.get("preferred_module"),
                "learning_style": request.form.get("learning_style")
            })

        # Appel au Path Planning
        if profiling_result and "error" not in profiling_result:
            planning_result = path_planning_agent.plan_path(profiling_result)
        
        # Appel au Content Generator LLM
         # ─── Content Generation LLM ───
        if planning_result and "planned_path" in planning_result:
            planned_path = planning_result["planned_path"]

            content_results = content_llm.generate_learning_content(
                profile=profiling_result,
                planned_path=planned_path
            )
        # Appel au Recommendation Agent
        # Dans  la  route POST, après le content generator :
        if planning_result and "planned_path" in planning_result:
            rec_results = rec_agent.recommend(profiling_result, planning_result["planned_path"], generated_content=content_results)
        # Appel au XAI Agent
        if rec_results:
            xai_agent = XAIAgent(profiling_agent)
            xai_results = xai_agent.explain(profiling_result, planning_result["planned_path"], rec_results)
    modules = sorted(data["courses"]["code_module"].unique())

    return render_template(
        "index.html",
        student_type=student_type,
        profiling_result=profiling_result,
        planning_result=planning_result,
        content_results=content_results,
        rec_results=rec_results,
        xai_results=xai_results,
        modules=modules
    )

if __name__ == "__main__":
    app.run(debug=True)