"""
modules/complaints/ml/duplicate_detection.py
─────────────────────────────────────────────────────────
Near-duplicate complaint detection via TF-IDF cosine similarity.

Requires scikit-learn (already in requirements.txt).
Falls back gracefully if sklearn is not yet installed.

Integration note: swap the ``complaints`` parameter for a DB
query result when the backend is ready.
─────────────────────────────────────────────────────────
"""

from __future__ import annotations
from typing import TypedDict


class DuplicateMatch(TypedDict):
    complaint_id: str
    title: str
    similarity: float   # 0.0 – 1.0


def find_duplicates(
    new_title: str,
    new_description: str,
    complaints: list[dict],
    threshold: float = 0.55,
    top_n: int = 3,
) -> list[DuplicateMatch]:
    """
    Compare a new complaint against an existing list and return likely duplicates.

    Parameters
    ----------
    new_title       : title of the incoming complaint
    new_description : description of the incoming complaint
    complaints      : list of complaint dicts — each must have 'id', 'title', 'description'
    threshold       : minimum cosine similarity to flag as a potential duplicate (default 0.55)
    top_n           : maximum number of matches to return

    Returns
    -------
    List of DuplicateMatch sorted by similarity descending.
    Returns an empty list when no duplicates are found or sklearn is unavailable.

    Integration note
    ----------------
    Replace ``complaints`` with a real DB query when the backend is ready.
    The return type contract stays the same.
    """
    if not complaints:
        return []

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
    except ImportError:
        # scikit-learn not yet installed — graceful degradation
        return []

    new_text = f"{new_title} {new_description}".lower().strip()
    existing_texts = [
        f"{c.get('title', '')} {c.get('description', '')}".lower().strip()
        for c in complaints
    ]

    corpus = [new_text] + existing_texts
    try:
        vectorizer = TfidfVectorizer(
            min_df=1,
            stop_words="english",
            ngram_range=(1, 2),
            norm="l2",          # cosine = dot product after L2 normalisation
        )
        tfidf = vectorizer.fit_transform(corpus)
    except ValueError:
        # Corpus too small or all stop-words
        return []

    new_vec = tfidf[0]
    existing_vecs = tfidf[1:]

    # Cosine similarity: (existing_vecs · new_vec.T) — both already L2-normed
    similarities = (existing_vecs * new_vec.T).toarray().flatten()

    results: list[DuplicateMatch] = []
    for idx, sim in enumerate(similarities):
        if sim >= threshold:
            c = complaints[idx]
            results.append(
                DuplicateMatch(
                    complaint_id=c.get("id", f"UNK-{idx}"),
                    title=c.get("title", "Unknown"),
                    similarity=round(float(sim), 3),
                )
            )

    results.sort(key=lambda r: r["similarity"], reverse=True)
    return results[:top_n]