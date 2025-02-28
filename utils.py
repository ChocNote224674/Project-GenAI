"""
Ce fichier sert à stocker les fonctions utilitaires et calculs de métriques.
"""

import os
from typing import Dict

from sklearn.metrics.pairwise import cosine_similarity
from bert_score import score as bert_score
from nltk.translate.meteor_score import meteor_score  # Import déplacé ici

from config import TABLE_NAME
from database import connect_db
from agents import compute_embedding


def get_random_questions(n: int):
    """Récupère n questions aléatoires depuis la base de données."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT question, answer FROM {TABLE_NAME} ORDER BY RANDOM() LIMIT %s", (n,))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data


def get_random_qcm(n: int, focus_area: str = None):
    """Récupère n questions à choix multiples aléatoires, filtrées par focus_area si fourni."""
    conn = connect_db()
    cursor = conn.cursor()

    if focus_area:
        cursor.execute(
            f"""SELECT question, answer, focus_area
            FROM {TABLE_NAME}
            WHERE focus_area = %s ORDER BY RANDOM() LIMIT %s""",
            (focus_area, n)
        )
    else:
        cursor.execute(
            f"SELECT question, answer, focus_area FROM {TABLE_NAME} ORDER BY RANDOM() LIMIT %s",
            (n,)
        )

    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data


def jaccard_similarity(text1: str, text2: str) -> float:
    """Calcule la similarité de Jaccard entre deux textes."""
    set1, set2 = set(text1.split()), set(text2.split())
    return len(set1 & set2) / len(set1 | set2) if set1 | set2 else 0.0


def assess_response_metrics(
    query: str, reference_answer: str, generated_response: str
) -> Dict[str, float]:
    """Évalue les similarités et la qualité de la réponse générée."""

    embeddings = {
        "query": compute_embedding(query),
        "reference": compute_embedding(reference_answer),
        "generated": compute_embedding(generated_response),
    }

    cosine_scores = {
        "reference": cosine_similarity([embeddings["query"]], [embeddings["reference"]])[0][0],
        "generated": cosine_similarity([embeddings["query"]], [embeddings["generated"]])[0][0],
    }

    jaccard_score = jaccard_similarity(reference_answer, generated_response)

    meteor = meteor_score([reference_answer], generated_response)

    # Correction du problème d'affectation avec bert_score
    _, _, f1_score = bert_score(
        [generated_response], [reference_answer], lang="en")

    return {
        "cosine_similarity": {k: round(v, 4) for k, v in cosine_scores.items()},
        "jaccard_similarity": round(jaccard_score, 4),
        "meteor_score": round(meteor, 4),
        "bert_score": round(f1_score.mean().item(), 4),
    }


def is_feedback_file_empty(file_path: str) -> bool:
    """Vérifie si un fichier de feedback est vide ou inexistant."""
    return not os.path.exists(file_path) or os.stat(file_path).st_size == 0
