# content_generator_rag_local.py
import re
import os
import subprocess
import json
from langchain_classic.vectorstores import FAISS
from langchain_classic.embeddings import HuggingFaceEmbeddings
from langchain_classic.prompts import PromptTemplate
from langchain_classic.schema import Document

class OllamaLocal:
    def __init__(self, model_name="gemma3:1b"):
        self.model = model_name
        self.ollama_path = r"C:\Users\user\AppData\Local\Programs\Ollama\ollama.exe"

    def generate(self, prompts: list[str]):
        generations = []
        for prompt in prompts:
            try:
                result = subprocess.run(
                    [self.ollama_path, "run", self.model],
                    input=prompt.encode(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True
                )
                text_output = result.stdout.decode().strip()
            except subprocess.CalledProcessError as e:
                text_output = f"Error: {e.stderr.decode().strip()}"
            generations.append([SimpleGeneration(text_output)])
        return SimpleResponse(generations)
    
class SimpleGeneration:
    def __init__(self, text):
        self.text = text

class SimpleResponse:
    def __init__(self, generations):
        self.generations = generations

# --- Générateur de contenu RAG ---
class ContentGeneratorRAG:
    def __init__(self, model_name="gemma3:1b", index_path="faiss_index"):
        self.model_name = model_name
        self.index_path = index_path
        self.llm = OllamaLocal(model_name=model_name)
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        if os.path.exists(index_path):
            self.vectorstore = FAISS.load_local(index_path, self.embeddings, allow_dangerous_deserialization=True)
        else:
            docs = self._get_sample_documents()
            self.build_index(docs)

    def _get_sample_documents(self):
        return [
            Document(page_content="Computer science studies computation, algorithms, data structures, software, and AI.", metadata={"module": "CCC"}),
            Document(page_content="Mathematics focuses on numbers, logic, algebra, calculus, and discrete structures used in computing.", metadata={"module": "DDD"}),
            Document(page_content="Physics studies matter, motion, energy, and forces, forming foundations for engineering and simulation.", metadata={"module": "EEE"}),
            Document(page_content="Biology studies living organisms, systems, evolution, and data-driven biological analysis.", metadata={"module": "FFF"}),
            Document(page_content="Social sciences analyze societies, behavior, economics, and human interaction.", metadata={"module": "GGG"}),
        ]

    def build_index(self, docs):
        self.vectorstore = FAISS.from_documents(docs, self.embeddings)
        self.vectorstore.save_local(self.index_path)
        print(f"✅ Index FAISS créé : {self.index_path}")

    def generate_learning_content(self, profile, planned_path, top_k=3):
        if not self.vectorstore:
            raise ValueError("Index FAISS non disponible")

        retriever = self.vectorstore.as_retriever(search_kwargs={"k": top_k})
        context_docs = retriever._get_relevant_documents(
            f"Planned path modules: {', '.join(planned_path)}. Student profile: {profile}",
            run_manager=None
        )
        context_text = "\n".join([doc.page_content for doc in context_docs])

        # Prompt template avec JSON échappé
        prompt = PromptTemplate(
            input_variables=["context", "profile", "planned_path"],
            template="""
You are an educational AI assistant.

Student profile:
{profile}

Planned learning path:
{planned_path}

Relevant materials:
{context}

Tasks:
1. Explain the learning path briefly.
2. Define learning objectives.
3. Create 3 quiz questions with answers.

Important instructions:
- Do NOT ask for additional information from the student.
- Only return the requested explanation, objectives, and quiz questions.

Output in JSON format only:
{{
    "explanation_path": "explanation text...",
    "learning_objectives": ["...", "..."],
    "quizzes": [
        {{"question": "...", "answer": "..."}},
        {{"question": "...", "answer": "..."}},
        {{"question": "...", "answer": "..."}}
    ]
}}
"""
        )

        prompt_text = prompt.format(
            context=context_text,
            profile=profile,
            planned_path=", ".join(planned_path)
        )

        # Génération
        response = self.llm.generate([prompt_text])
        response_text = response.generations[0][0].text

        # Essayer de parser JSON pour quizzes
        quizzes = []
        try:
            response_json = json.loads(response_text)
            quizzes = response_json.get("quizzes", [])
        except json.JSONDecodeError:
            # fallback : regex si Ollama ne renvoie pas JSON strict
            question_pattern = r"\d+\.\s*\*\*Question:\*\*\s*(.+?)\s*\*\*Answer:\*\*\s*(.+?)(?=\d+\.|$)"
            matches = re.findall(question_pattern, response_text, re.DOTALL)
            for i, (q, a) in enumerate(matches[:3], 1):
                quizzes.append({"number": i, "question": q.strip(), "answer": a.strip()})

        return {
            "generated_content": response_text,
            "model_used": self.model_name,
            "source_documents": [doc.metadata.get("module", "?") for doc in context_docs],
            "quizzes_structured": quizzes
        }

# --- Test rapide ---
if __name__ == "__main__":
    gen = ContentGeneratorRAG()
    profile = {"learning_style": "visual", "risk_level": "medium"}
    planned_path = ["CCC", "DDD", "EEE"]
    result = gen.generate_learning_content(profile, planned_path)
    print("=== Generated Content ===")
    print(result["generated_content"])
    print("Quizzes:", result["quizzes_structured"])
    print("Source docs:", result["source_documents"])
