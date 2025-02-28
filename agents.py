"""
This module provides functionalities for generating embeddings,
AI-assisted responses, and QCM using generative AI.
"""

import random
import logging
from typing import List

from sentence_transformers import SentenceTransformer
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from config import API_KEY

# Configuration du logging
logging.basicConfig(level=logging.INFO)

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
    """
    Génère une réponse enrichie en utilisant un modèle d'IA.

    Args:
        question (str): La question posée.
        context (str): Le contexte fourni.
        language (str): La langue de réponse.

    Returns:
        str: La réponse générée.
    """
    prompt = ChatPromptTemplate.from_template(
        """You are a medical AI assistant.
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


def reword_correct_answer(
        agent,
        question: str,
        correct_answer: str,
        focus_area: str) -> str:
    """
    Reformule la bonne réponse sous forme d'une seule phrase.

    Args:
        agent: Modèle d'IA génératif.
        question (str): La question du QCM.
        correct_answer (str): La réponse correcte.
        focus_area (str): Thème de la question.

    Returns:
        str: Réponse reformulée.
    """
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
        return response.strip()

    if response and isinstance(response.content, str):
        return response.content.strip()

    return correct_answer  # Fallback


def generate_false_answers(
        agent,
        question: str,
        correct_answer: str,
        focus_area: str) -> List[str]:
    """
    Génère exactement 3 réponses incorrectes mais plausibles.

    Args:
        agent: Modèle d'IA génératif.
        question (str): La question du QCM.
        correct_answer (str): La réponse correcte.
        focus_area (str): Thème de la question.

    Returns:
        List[str]: Liste de trois réponses incorrectes.
    """
    prompt = f"""Generate **exactly three** incorrect but plausible answers
    for the following question:
    - Each incorrect answer must be a **single, short sentence** similar to the correct answer.
    - The incorrect answers should be **believable but factually incorrect**.
    - Do **NOT** include explanations or additional details.
    - **Topic:** {focus_area}
    - **Question:** {question}
    - **Correct Answer:** {correct_answer}
    - Provide exactly three incorrect answers, separated by '###'."""

    response = agent.invoke(prompt)
    logging.info("Generated false answers: %s", response)

    if isinstance(response, str):
        false_answers = [answer.strip() for answer in response.split("###")]
    elif response and isinstance(response.content, str):
        false_answers = [answer.strip()
                         for answer in response.content.split("###")]
    else:
        return []  # Return an empty list if the response is invalid

    # S'assurer d'avoir exactement 3 réponses incorrectes
    while len(false_answers) < 3:
        false_answers.append(f"Incorrect answer {len(false_answers) + 1}")

    return false_answers[:3]


def create_mcq(question: str, correct_answer: str, focus_area: str) -> dict:
    """
    Crée une question à choix multiples avec 3 fausses réponses et 1 bonne réponse.

    Args:
        question (str): La question du QCM.
        correct_answer (str): La réponse correcte.
        focus_area (str): Thème de la question.

    Returns:
        dict: Contient la question, les options mélangées et la réponse correcte.
    """
    reformulated_correct_answer = reword_correct_answer(
        ai_model, question, correct_answer, focus_area)
    false_answers = generate_false_answers(
        ai_model, question, reformulated_correct_answer, focus_area)

    # S'assurer d'avoir exactement 3 réponses incorrectes
    while len(false_answers) < 3:
        false_answers.append(f"Incorrect alternative {len(false_answers) + 1}")

    options = false_answers + [reformulated_correct_answer]
    random.shuffle(options)  # Mélanger les options

    return {
        "question": question,
        "options": options,
        "correct_answer": reformulated_correct_answer
    }
