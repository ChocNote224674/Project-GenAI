import psycopg2
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

hf_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")


# Connexion PostgreSQL
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)
cursor = conn.cursor()


BATCH_SIZE = 100 

# Récupérer toutes les questions sans embeddings
cursor.execute("SELECT id, question FROM ya_table_project WHERE embedding IS NULL")
questions = cursor.fetchall()

if not questions:
    print("Toutes les questions ont déjà des embeddings.")
else:

    # Barre de progression
    with tqdm(total=len(questions), desc="Traitement des embeddings", unit="question") as pbar:
        for i in range(0, len(questions), BATCH_SIZE):
            batch = questions[i : i + BATCH_SIZE]
            batch_ids = [q[0] for q in batch]
            batch_questions = [q[1] for q in batch]

            try:
                embedding_vectors = [hf_model.encode(q).tolist() for q in batch_questions]
            except Exception as e:
                print(f"Erreur inattendue avec Hugging Face : {e}")
                continue  

            # Stockage dans PostgreSQL en batch
            update_values = [(embedding_vectors[idx], batch_ids[idx]) for idx in range(len(batch))]
            cursor.executemany("UPDATE ya_table_project SET embedding = %s WHERE id = %s", update_values)
            conn.commit()

            # Mise à jour de la barre de progression
            pbar.update(len(batch))

    print("Tous les embeddings ont été stockés.")

cursor.close()
conn.close()

