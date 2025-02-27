import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agents import compute_embedding, generate_ai_response, create_mcq
from retrieve import find_best_match
from utils import get_random_qcm

# Initialize FastAPI
app = FastAPI()

# Model for API requests
class QueryRequest(BaseModel):
    question: str
    temperature: float = 0.7
    language: str = "english"


# Endpoint to get sources
@app.post("/get_sources")
def get_sources(request: QueryRequest):
    start_time = time.time()
    query_embedding = compute_embedding(request.question)
    best_match = find_best_match(request.question, query_embedding)

    if best_match:
        response_time = time.time() - start_time
        print(f"Response time for get_sources: {response_time:.4f} seconds")
        return best_match

    response_time = time.time() - start_time
    print(f"Response time for get_sources: {response_time:.4f} seconds")
    raise HTTPException(status_code=404, detail="No relevant document found.")


# Endpoint to generate an enriched answer with Gemini
@app.post("/answer")
def answer(request: QueryRequest):
    start_time = time.time()
    query_embedding = compute_embedding(request.question)
    best_match = find_best_match(request.question, query_embedding)

    if not best_match:
        # Call the LLM to generate a response instead
        llm_response = generate_ai_response(request.question,"AI generation", request.language)
        response_time = time.time() - start_time
        print(f"Response time for answer (no match found): {response_time:.4f} seconds")
        
        return {
            "answer": llm_response,
            "source": "Generated by AI",
            "focus_area": "General Knowledge",
            "similarity": None,
            "metrics": {},
            "response_time": round(response_time, 4)
        }

    # Generate AI response based on retrieved match
    response = generate_ai_response(request.question, best_match['answer'], request.language)
    
    metrics = {
        "cosine_similarity": best_match["cosine_similarity"],
        "jaccard_similarity": best_match["jaccard_similarity"],
        "meteor_score": best_match["meteor_score"],
        "bert_score": best_match["bert_score"],
    }
    
    print(f"Metrics: {metrics}")
    response_time = time.time() - start_time
    print(f"Response time for answer (with match found): {response_time:.4f} seconds")
    
    return {
        "answer": response,
        "source": best_match["source"],
        "focus_area": best_match["focus_area"],
        "similarity": best_match["cosine_similarity"],
        "metrics": metrics,
        "response_time": round(response_time, 4)
    }


@app.get("/qcm")
def get_qcm(n: int = 5):
    """Returns a set of dynamically generated multiple-choice questions."""
    questions = get_random_qcm(n)  # Fetch random QCM questions from DB
    mcq_list = [create_mcq(q[0], q[1], q[2]) for q in questions]  # Process each question
    return {"questions": mcq_list}