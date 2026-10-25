
"""Trained NLP classifier for SafeSense AI food complaints."""

from pathlib import Path
from typing import TypedDict

import joblib

CATEGORIES = [
    "Hygiene",
    "Food Quality",
    "Expired Food",
    "Suspected Adulteration",
    "Foreign Object",
    "Packaging",
    "Mislabeling",
    "Other",
]

MODEL_PATH = (
    Path(__file__).resolve().parent
    / "artifacts"
    / "complaint_classifier.joblib"
)

_model_bundle = None
_model_load_attempted = False


class PredictionResult(TypedDict):
    predicted_category: str
    confidence: float
    top_keywords: list[str]
    all_scores: dict[str, float]


def _load_model():
    """Load the saved model once, when first needed."""
    global _model_bundle, _model_load_attempted

    if _model_load_attempted:
        return _model_bundle

    _model_load_attempted = True

    if not MODEL_PATH.exists():
        return None

    try:
        bundle = joblib.load(MODEL_PATH)

        if not isinstance(bundle, dict) or "pipeline" not in bundle:
            return None

        pipeline = bundle["pipeline"]

        if not hasattr(pipeline, "predict_proba"):
            return None

        _model_bundle = bundle
        return _model_bundle

    except (OSError, ValueError, KeyError, AttributeError, EOFError):
        return None


def predict_category(title: str, description: str) -> PredictionResult:
    """Predict complaint category using the trained TF-IDF model."""

    title = (title or "").strip()
    description = (description or "").strip()
    text = f"{title}. {description}".strip(" .")

    empty_scores = {category: 0.0 for category in CATEGORIES}

    if not text:
        return PredictionResult(
            predicted_category="Other",
            confidence=0.0,
            top_keywords=[],
            all_scores=empty_scores,
        )

    bundle = _load_model()

    if bundle is None:
        # Do not pretend that a trained prediction was made.
        return PredictionResult(
            predicted_category="Other",
            confidence=0.0,
            top_keywords=[],
            all_scores=empty_scores,
        )

    pipeline = bundle["pipeline"]

    try:
        probabilities = pipeline.predict_proba([text])[0]
        model_classes = list(pipeline.classes_)

        scores = {
            str(category): float(probability)
            for category, probability in zip(model_classes, probabilities)
        }

        best_index = int(probabilities.argmax())
        predicted_category = str(model_classes[best_index])

        # Extract the strongest words present in this complaint.
        vectorizer = pipeline.named_steps["tfidf"]
        vector = vectorizer.transform([text])
        feature_names = vectorizer.get_feature_names_out()
        active_indices = vector.nonzero()[1]

        ranked_indices = sorted(
            active_indices,
            key=lambda index: float(vector[0, index]),
            reverse=True,
        )

        top_keywords = [
            str(feature_names[index])
            for index in ranked_indices[:6]
        ]

        # Include all project categories, even if absent during training.
        all_scores = {
            category: round(scores.get(category, 0.0), 4)
            for category in CATEGORIES
        }

        return PredictionResult(
            predicted_category=(
                predicted_category
                if predicted_category in CATEGORIES
                else "Other"
            ),
            confidence=round(float(probabilities[best_index]), 4),
            top_keywords=top_keywords,
            all_scores=all_scores,
        )

    except (ValueError, KeyError, AttributeError, IndexError):
        return PredictionResult(
            predicted_category="Other",
            confidence=0.0,
            top_keywords=[],
            all_scores=empty_scores,
        )
