"""
This module provides functionalities for generating embeddings,
 AI-assisted responses and QCM using generative AI."""
from typing import List
import random
import re
from sentence_transformers import SentenceTransformer
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from config import API_KEY

# Chargement du modèle d'embedding
MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"
embedding_model = SentenceTransformer(MODEL_NAME)

# Initialisation du modèle d'IA générative
ai_model = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    temperature=0.5,
    google_api_key=API_KEY
)


def compute_embedding(text: str) -> List[float]:
    """Génère un vecteur d'embedding pour un texte donné."""
    return embedding_model.encode(text, normalize_embeddings=True).tolist()


def generate_ai_response(question: str, context: str, language: str) -> str:
    """Génère une réponse enrichie en utilisant un modèle d'IA."""
    prompt = ChatPromptTemplate.from_template(
        """ You are a medical AI assistant.
        Your goal is to provide accurate and well-structured responses.
        Guidelines:
        - Prioritize medically validated information.
        - Clarify ambiguous contexts before responding.
        - Use clear and professional language.
        - Cite sources when available.
       Question: {question}
       Context: {context}
       Language: {language}
        """
    )
    response = (prompt | ai_model).invoke({
        "question": question,
        "context": context,
        "language": language,
    })
    return response.content


def reword_correct_answer(agent, question, correct_answer, focus_area):
    """Reword the correct answer as a single sentence."""
    prompt = f"""Rephrase the correct answer as:
    - **A single, concise sentence** that matches the style of a QCM.
    - The sentence should be grammatically correct and natural.
    - Do NOT add explanations or extra details.
    - **Topic:** {focus_area}
    - **Question:** {question}
    - **Correct Answer:** {correct_answer}
    - Provide ONLY the reworded answer as a single, well-formed sentence."""
    response = agent.invoke(prompt)
    if isinstance(response, str):
        cleaned_response = response.strip()
    elif response and hasattr(response, "content"):
        cleaned_response = response.content.strip()
    else:
        return correct_answer  # Fallback if response is invalid
    cleaned_response = re.sub(r'\s+', ' ', cleaned_response).strip()

    return cleaned_response


def generate_false_answers(agent, question, correct_answer, focus_area):
    """Generate exactly 3 incorrect but plausible answers."""
    prompt = f"""Generate **exactly three** incorrect but plausible answers
    for the following question:
- Each incorrect answer must be a :
**single, short sentence** similar to the correct answer.
    - The incorrect answers should be **believable but factually incorrect**.
    - Do **NOT** include explanations or additional details.
    - **Topic:** {focus_area}
    - **Question:** {question}
    - **Correct Answer:** {correct_answer}
    - Provide exactly three incorrect answers, separated by '###'."""

    response = agent.invoke(prompt)

    # Debugging output
    print(f"🛠 Debug False Answers: {response}")

    if isinstance(response, str):
        raw_answers = [answer.strip() for answer in response.split("###")]
    elif response and hasattr(response, "content"):
        raw_answers = response.content.strip()
    else:
        return []  # Return an empty list if the response is invalid

    # Remove unwanted line breaks and extra spaces
    false_answers = [answer.strip() for answer in raw_answers.split("###")]

    # Ensure we get exactly 3 false answers
    while len(false_answers) < 3:
        false_answers.append(f"Incorrect answer {len(false_answers) + 1}")

    return false_answers[:3]


def create_mcq(question, correct_answer, focus_area):
    """Create a QCM with 3 false answers and 1 correct answer."""
    reformulated_correct_answer = reword_correct_answer(ai_model, question, correct_answer, focus_area)
    false_answers = generate_false_answers(ai_model, question, reformulated_correct_answer, focus_area)

    # Ensure we have exactly 3 false answers
    while len(false_answers) < 3:
        false_answers.append(f"Incorrect alternative {len(false_answers) + 1}")
    false_answers = false_answers[:3]

    options = false_answers + [reformulated_correct_answer]  # Combine correct and incorrect answers
    random.shuffle(options)  # Shuffle the options

    return {
        "question": question,
        "options": options,
        "correct_answer": reformulated_correct_answer
    }
