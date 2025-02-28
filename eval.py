"""
Chatbot Evaluation Script.

This script tests the chatbot on a set of random questions and computes
various evaluation metrics such as Cosine Similarity, Jaccard Similarity,
METEOR Score, and BERTScore.
"""

import warnings
import requests
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from bert_score import score as bert_score
from nltk.translate.meteor_score import meteor_score
from utils import get_random_questions
from agents import compute_embedding

# Ignore warnings
warnings.simplefilter("ignore")


def evaluate_chatbot(n):
    """Test the chatbot on n questions and compute evaluation metrics."""
    questions_answers = get_random_questions(n)
    cosine_similarities, jaccard_scores, meteor_scores, bert_scores_list = [], [], [], []

    print("\n--- Chatbot Evaluation ---\n")

    for i, (question, true_answer) in enumerate(questions_answers, 1):
        response = requests.post(
            "http://127.0.0.1:8000/answer",
            json={
                "question": question},
            timeout=500)

        if response.status_code == 200:
            data = response.json()
            predicted_answer = data.get("answer", "")

            # Cosine Similarity
            true_embedding = compute_embedding(true_answer)
            predicted_embedding = compute_embedding(predicted_answer)
            cosine_sim = cosine_similarity(
                [true_embedding], [predicted_embedding])[0][0]
            cosine_similarities.append(cosine_sim)

            # Jaccard Similarity
            true_tokens, pred_tokens = set(
                true_answer.split()), set(
                predicted_answer.split())
            jaccard = len(true_tokens & pred_tokens) / len(true_tokens |
                                                           pred_tokens) if true_tokens | pred_tokens else 0
            jaccard_scores.append(jaccard)

            # METEOR Score
            meteor = meteor_score([true_answer.split()],
                                  predicted_answer.split())
            meteor_scores.append(meteor)

            # BERT Score
            _, _, f1_score = bert_score(
                [predicted_answer], [true_answer], lang="en")
            bert_scores_list.append(f1_score.mean().item())

            # Affichage des résultats pour chaque requête
            print(f"**Question {i}:** {question}")
            print(f"**Réponse attendue:** {true_answer}")
            print(f"**Réponse du chatbot:** {predicted_answer}")
            print(f"**Cosine Similarity:** {cosine_sim:.4f}")
            print(f"**Jaccard Similarity:** {jaccard:.4f}")
            print(f"**METEOR Score:** {meteor:.4f}")
            print(f" **BERT Score:** {f1_score.mean().item():.4f}\n")
            print("-" * 60)

    # Compute averages
    results = {
        "cosine_similarity": np.mean(cosine_similarities),
        "jaccard_similarity": np.mean(jaccard_scores),
        "meteor_score": np.mean(meteor_scores),
        "bert_score": np.mean(bert_scores_list)
    }

    #  Affichage final des moyennes
    print("\n--- **Final Chatbot Evaluation Summary** ---")
    for metric, value in results.items():
        print(f"{metric.replace('_', ' ').title()} Average: {value:.4f}")

    return results


if __name__ == "__main__":
    evaluate_chatbot(10)
