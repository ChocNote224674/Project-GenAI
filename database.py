"""
Database connection and query functions.

This module establishes a connection to a PostgreSQL database
and provides functions for retrieving cached embeddings.
"""

# Standard library
import json
from functools import lru_cache
from typing import List, Tuple

# Third-party libraries
import psycopg2
from fastapi import HTTPException

# Internal modules
from config import TABLE_NAME, DB_PASSWORD, DB_USER, DB_NAME, DB_HOST, DB_PORT


def connect_db():
    """Establish a secure connection to PostgreSQL."""
    try:
        return psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"DB connection error: {
                str(e)}") from e


@lru_cache(maxsize=1000)
def get_all_embeddings() -> List[Tuple[str, str, str, List[float]]]:
    """Retrieve cached embeddings from PostgreSQL to reduce query load."""
    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT answer, source, focus_area, embedding "
                f"FROM {TABLE_NAME} WHERE embedding IS NOT NULL"
            )
            rows = cur.fetchall()

        cleaned_rows = []
        for row in rows:
            try:
                embedding = (
                    json.loads(row[3]) if isinstance(row[3], str)
                    else row[3] if isinstance(row[3], list) else []
                )
                cleaned_rows.append((row[0], row[1], row[2], embedding))
            except json.JSONDecodeError:
                print(f"Erreur de décodage JSON pour l'entrée : {row[0]}")

        return cleaned_rows
    finally:
        conn.close()
