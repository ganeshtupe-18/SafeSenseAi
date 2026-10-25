
"""Train and evaluate the SafeSense AI complaint classifier."""

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

MODEL_PATH = (
    Path(__file__).resolve().parent
    / "artifacts"
    / "complaint_classifier.joblib"
)


def train(data_path: Path, model_path: Path = MODEL_PATH):
    df = pd.read_csv(data_path)

    required = {"title", "description", "category"}
    if not required.issubset(df.columns):
        raise ValueError(f"CSV must contain columns: {sorted(required)}")

    df = df.dropna(subset=["category"]).copy()
    df["title"] = df["title"].fillna("").astype(str)
    df["description"] = df["description"].fillna("").astype(str)
    df["category"] = df["category"].astype(str).str.strip()
    df["text"] = (df["title"] + ". " + df["description"]).str.strip(" .")
    df = df[(df["text"] != "") & (df["category"] != "")]

    counts = df["category"].value_counts()
    if len(counts) < 2 or counts.min() < 2:
        raise ValueError("At least 2 examples per category are required.")

    train_text, test_text, y_train, y_test = train_test_split(
        df["text"],
        df["category"],
        test_size=0.2,
        random_state=42,
        stratify=df["category"],
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            lowercase=True,
            strip_accents="unicode",
            ngram_range=(1, 2),
            sublinear_tf=True,
        )),
        ("classifier", LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=42,
        )),
    ])

    pipeline.fit(train_text, y_train)
    predictions = pipeline.predict(test_text)

    accuracy = accuracy_score(y_test, predictions)
    macro_f1 = f1_score(
        y_test, predictions, average="macro", zero_division=0
    )
    report = classification_report(
        y_test, predictions, output_dict=True, zero_division=0
    )
    matrix = confusion_matrix(
        y_test, predictions, labels=pipeline.classes_
    )

    model_path.parent.mkdir(parents=True, exist_ok=True)
    bundle = {
        "pipeline": pipeline,
        "model_version": "1.0",
        "categories": list(pipeline.classes_),
        "metrics": {
            "accuracy": float(accuracy),
            "macro_f1": float(macro_f1),
        },
    }
    joblib.dump(bundle, model_path)

    report_path = model_path.parent / "evaluation_report.json"
    report_path.write_text(json.dumps({
        "rows": len(df),
        "train_rows": len(train_text),
        "test_rows": len(test_text),
        "accuracy": float(accuracy),
        "macro_f1": float(macro_f1),
        "classification_report": report,
        "confusion_matrix_labels": list(pipeline.classes_),
        "confusion_matrix": matrix.tolist(),
        "note": "Synthetic data scores do not establish real-world performance.",
    }, indent=2), encoding="utf-8")

    print(f"Model saved: {model_path}")
    print(f"Evaluation report saved: {report_path}")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Macro F1: {macro_f1:.4f}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--model-out", type=Path, default=MODEL_PATH)
    args = parser.parse_args()
    train(args.data, args.model_out)


if __name__ == "__main__":
    main()
