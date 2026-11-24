"""Train, compare, calibrate, evaluate, and save the Part B models."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.frozen import FrozenEstimator
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.decomposition import TruncatedSVD

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from password_risk.baseline import luds_is_strong, luds_predict
from password_risk.data import generate_strong_passwords, load_leaked_passwords
from password_risk.features import build_feature_union


SEED = 42


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def evaluate_predictions(name, y_true, predictions, probabilities, latency_ms):
    tn, fp, fn, tp = confusion_matrix(y_true, predictions, labels=[0, 1]).ravel()
    result = {
        "model": name,
        "accuracy": accuracy_score(y_true, predictions),
        "precision": precision_score(y_true, predictions, zero_division=0),
        "recall": recall_score(y_true, predictions, zero_division=0),
        "f1": f1_score(y_true, predictions, zero_division=0),
        "latency_ms_per_password": latency_ms,
        "true_negative": int(tn),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_positive": int(tp),
    }
    if probabilities is not None:
        result.update(
            {
                "roc_auc": roc_auc_score(y_true, probabilities),
                "average_precision": average_precision_score(y_true, probabilities),
                "brier_score": brier_score_loss(y_true, probabilities),
            }
        )
    return result


def timed_predictions(model, X):
    start = time.perf_counter()
    probabilities = model.predict_proba(X)[:, 1]
    elapsed = time.perf_counter() - start
    return probabilities, elapsed * 1000 / len(X)


def model_size_bytes(model, directory: Path, name: str) -> int:
    path = directory / f"_{name}_candidate.joblib"
    joblib.dump(model, path, compress=3)
    size = path.stat().st_size
    path.unlink()
    return size


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--leaked", required=True, help="Path to rockyou.txt or rockyou.txt.tar.gz")
    parser.add_argument("--limit", type=int, default=50000, help="Unique leaked examples to load")
    parser.add_argument("--ngram-features", type=int, default=3000)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    print("Loading and deduplicating leaked examples...")
    leaked = load_leaked_passwords(args.leaked, args.limit, seed=SEED, strategy="reservoir")
    strong = generate_strong_passwords(len(leaked), seed=SEED)
    overlap = set(leaked).intersection(strong)
    if overlap:
        strong = [password for password in strong if password not in overlap]
        strong.extend(generate_strong_passwords(len(leaked) + len(overlap), seed=SEED + 1)[-len(overlap):])

    X = np.asarray(leaked + strong, dtype=object)
    y = np.asarray([1] * len(leaked) + [0] * len(strong), dtype=np.int8)
    X_train_cal, X_test, y_train_cal, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=SEED
    )
    X_train, X_cal, y_train, y_cal = train_test_split(
        X_train_cal, y_train_cal, test_size=0.20, stratify=y_train_cal, random_state=SEED
    )

    models = {
        "logistic_regression": Pipeline(
            [
                ("features", build_feature_union(args.ngram_features)),
                (
                    "classifier",
                    LogisticRegression(
                        max_iter=1000,
                        C=2.0,
                        class_weight="balanced",
                        random_state=SEED,
                    ),
                ),
            ]
        ),
        "random_forest": Pipeline(
            [
                ("features", build_feature_union(args.ngram_features)),
                ("reduce", TruncatedSVD(n_components=48, random_state=SEED)),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=200,
                        max_depth=24,
                        min_samples_leaf=2,
                        class_weight="balanced_subsample",
                        n_jobs=-1,
                        random_state=SEED,
                    ),
                ),
            ]
        ),
    }

    results = []
    calibrated_models = {}
    complex_leaked_mask = np.asarray(
        [actual == 1 and luds_is_strong(str(password)) for password, actual in zip(X_test, y_test)]
    )
    for name, base_model in models.items():
        print(f"Training {name}...")
        base_model.fit(X_train, y_train)
        calibrated = CalibratedClassifierCV(FrozenEstimator(base_model), method="sigmoid")
        calibrated.fit(X_cal, y_cal)
        probabilities, latency = timed_predictions(calibrated, X_test)
        predictions = (probabilities >= 0.5).astype(np.int8)
        row = evaluate_predictions(name, y_test, predictions, probabilities, latency)
        row["complex_leaked_recall"] = (
            float(predictions[complex_leaked_mask].mean()) if complex_leaked_mask.any() else np.nan
        )
        row["model_size_bytes"] = model_size_bytes(calibrated, args.output, name)
        results.append(row)
        calibrated_models[name] = calibrated

    start = time.perf_counter()
    baseline_predictions = luds_predict(X_test)
    baseline_latency = (time.perf_counter() - start) * 1000 / len(X_test)
    baseline_row = evaluate_predictions(
        "luds_baseline", y_test, baseline_predictions, None, baseline_latency
    )
    baseline_row["complex_leaked_recall"] = (
        float(baseline_predictions[complex_leaked_mask].mean()) if complex_leaked_mask.any() else np.nan
    )
    results.append(baseline_row)

    learned = sorted(results[:2], key=lambda row: row["f1"], reverse=True)
    if learned[0]["f1"] - learned[1]["f1"] <= 0.01:
        selected_name = "logistic_regression"
    else:
        selected_name = learned[0]["model"]
    selected = calibrated_models[selected_name]

    model_path = args.output / "password_risk_model.joblib"
    joblib.dump(selected, model_path, compress=3)
    digest = hashlib.sha256(model_path.read_bytes()).hexdigest()

    metrics = pd.DataFrame(results)
    metrics.to_csv(args.output / "metrics.csv", index=False)
    (args.output / "metrics.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )
    source_path = Path(args.leaked)
    manifest = {
        "selected_model": selected_name,
        "score_interpretation": "Estimated similarity to leaked-password patterns under the experimental training distribution; not a literal future breach probability.",
        "thresholds": {"strong": "<30%", "medium": "30%-70%", "weak": ">70%"},
        "seed": SEED,
        "dataset": {
            "source_file_name": source_path.name,
            "source_size_bytes": source_path.stat().st_size,
            "source_sha256": file_sha256(source_path),
            "unique_leaked_examples": len(leaked),
            "generated_strong_examples": len(strong),
            "train_examples": len(X_train),
            "calibration_examples": len(X_cal),
            "evaluation_examples": len(X_test),
            "complex_looking_leaked_evaluation_examples": int(complex_leaked_mask.sum()),
        },
        "feature_families": [
            "length",
            "character types",
            "character n-grams (2-4)",
            "empirical character entropy",
            "repetition and sequence indicators",
        ],
        "versions": {
            "python": sys.version.split()[0],
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "model_sha256": digest,
    }
    (args.output / "model_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    print("\nAggregate test results (raw passwords are not displayed):")
    print(metrics.to_string(index=False, float_format=lambda value: f"{value:.4f}"))
    print(f"\nSelected model: {selected_name}")
    print(f"Saved: {model_path}")


if __name__ == "__main__":
    main()
