"""
Module de recherche du meilleur texte correspondant à une requête
en utilisant des métriques de similarité (cosinus, Jaccard, METEOR, BERTScore).
"""

from typing import List, Optional  # Import standard en premier

import numpy as np  # Bibliothèque tierce
from sklearn.metrics.pairwise import cosine_similarity
from bert_score import score as bert_score
from nltk.translate.meteor_score import meteor_score

from utils import jaccard_similarity  # Imports internes en dernier
from database import get_all_embeddings


def find_best_match(query_text: str, query_embedding: List[float]) -> Optional[dict]:
    """Trouve la meilleure correspondance pour une requête donnée en utilisant plusieurs métriques de similarité."""

    rows = get_all_embeddings()
    if not rows:
        return None

    docs = [row[3] for row in rows]
    cosine_scores = cosine_similarity([query_embedding], docs)[0]
    best_idx = np.argmax(cosine_scores)

    if cosine_scores[best_idx] < 0.75:
        return None

    best_answer = rows[best_idx][0]

    # Calcul des métriques supplémentaires
    jaccard_score = jaccard_similarity(query_text, best_answer)
    meteor = meteor_score([best_answer.split()], query_text.split())

    # Correction de l'affectation de BERTScore
    _, _, f1_score = bert_score([query_text], [best_answer], lang="en")

    return {
        "answer": best_answer,
        "source": rows[best_idx][1],
        "focus_area": rows[best_idx][2],
        "cosine_similarity": round(cosine_scores[best_idx], 4),
        "jaccard_similarity": round(jaccard_score, 4),
        "meteor_score": round(meteor, 4),
        "bert_score": round(f1_score.mean().item(), 4)
    }
