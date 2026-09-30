from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.utils.class_weight import compute_sample_weight


RANDOM_STATE = 42
TARGET = "default_12m"
MINIMUM_RECALL = 0.80
IDENTIFIERS = ["loan_id", "application_id", "customer_id"]
EXCLUDED = IDENTIFIERS + ["application_date", TARGET]


def project_root() -> Path:
    script = Path(__file__).resolve()
    for candidate in [script.parent, *script.parents]:
        if (candidate / ".env").exists():
            return candidate
    return script.parents[2]


def customer_split(data: pd.DataFrame):
    customers = data.groupby("customer_id", as_index=False)[TARGET].max()
    development_customers, test_customers = train_test_split(
        customers,
        test_size=0.20,
        random_state=RANDOM_STATE,
        stratify=customers[TARGET],
    )
    train_customers, validation_customers = train_test_split(
        development_customers,
        test_size=0.25,
        random_state=RANDOM_STATE,
        stratify=development_customers[TARGET],
    )
    train_ids = set(train_customers["customer_id"])
    validation_ids = set(validation_customers["customer_id"])
    test_ids = set(test_customers["customer_id"])
    if train_ids & validation_ids or train_ids & test_ids or validation_ids & test_ids:
        raise RuntimeError("Customer leakage detected across data splits.")
    return (
        data[data["customer_id"].isin(train_ids)].copy(),
        data[data["customer_id"].isin(validation_ids)].copy(),
        data[data["customer_id"].isin(test_ids)].copy(),
    )


def choose_threshold(y_true: pd.Series, probability: np.ndarray) -> float:
    precision, recall, thresholds = precision_recall_curve(y_true, probability)
    candidates = pd.DataFrame({
        "threshold": thresholds,
        "precision": precision[:-1],
        "recall": recall[:-1],
    })
    candidates = candidates[candidates["recall"] >= MINIMUM_RECALL]
    if candidates.empty:
        return 0.50
    best = candidates.sort_values(
        ["precision", "recall", "threshold"], ascending=[False, False, False]
    ).iloc[0]
    return float(best["threshold"])


def calculate_metrics(y_true, probability, threshold: float) -> dict:
    predicted = (probability >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, predicted).ravel()
    return {
        "threshold": float(threshold),
        "roc_auc": float(roc_auc_score(y_true, probability)),
        "pr_auc": float(average_precision_score(y_true, probability)),
        "precision": float(precision_score(y_true, predicted, zero_division=0)),
        "recall": float(recall_score(y_true, predicted, zero_division=0)),
        "f1": float(f1_score(y_true, predicted, zero_division=0)),
        "accuracy": float(accuracy_score(y_true, predicted)),
        "brier_score": float(brier_score_loss(y_true, probability)),
        "log_loss": float(log_loss(y_true, probability)),
        "true_negatives": int(tn),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "true_positives": int(tp),
    }


def make_preprocessor(numeric: list[str], categorical: list[str]) -> ColumnTransformer:
    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    return ColumnTransformer([
        ("numeric", numeric_pipeline, numeric),
        ("categorical", categorical_pipeline, categorical),
    ], sparse_threshold=0)


def main() -> None:
    root = project_root()
    dataset = root / "data" / "processed" / "credit_risk_training_dataset.csv"
    output = root / "backend" / "ml" / "artifacts" / "model_comparison_v1"
    output.mkdir(parents=True, exist_ok=True)
    if not dataset.is_file():
        raise FileNotFoundError(f"Dataset not found: {dataset}")

    data = pd.read_csv(dataset, parse_dates=["application_date"])
    data["county_code"] = data["county_code"].astype("string")
    data["adverse_listing_flag"] = data["adverse_listing_flag"].astype("string")
    features = [column for column in data.columns if column not in EXCLUDED]
    categorical = data[features].select_dtypes(
        include=["object", "string", "category", "bool"]
    ).columns.tolist()
    numeric = [column for column in features if column not in categorical]

    train, validation, test = customer_split(data)
    X_train, y_train = train[features], train[TARGET]
    X_validation, y_validation = validation[features], validation[TARGET]
    X_test, y_test = test[features], test[TARGET]
    print(f"Train      : {len(train):,} rows, {int(y_train.sum()):,} defaults")
    print(f"Validation : {len(validation):,} rows, {int(y_validation.sum()):,} defaults")
    print(f"Test       : {len(test):,} rows, {int(y_test.sum()):,} defaults")

    model_specs = {
        "logistic_regression": LogisticRegression(
            class_weight="balanced", max_iter=3000, solver="liblinear",
            random_state=RANDOM_STATE,
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=500, max_depth=10, min_samples_leaf=5,
            max_features="sqrt", class_weight="balanced_subsample",
            n_jobs=-1, random_state=RANDOM_STATE,
        ),
        "gradient_boosting": HistGradientBoostingClassifier(
            learning_rate=0.05, max_iter=300, max_leaf_nodes=15,
            min_samples_leaf=20, l2_regularization=1.0,
            random_state=RANDOM_STATE,
        ),
    }

    fitted = {}
    validation_rows = []
    for name, estimator in model_specs.items():
        print(f"Training {name}...")
        pipeline = Pipeline([
            ("preprocessor", make_preprocessor(numeric, categorical)),
            ("model", estimator),
        ])
        fit_parameters = {}
        if name == "gradient_boosting":
            fit_parameters["model__sample_weight"] = compute_sample_weight(
                class_weight="balanced", y=y_train
            )
        pipeline.fit(X_train, y_train, **fit_parameters)
        probability = pipeline.predict_proba(X_validation)[:, 1]
        threshold = choose_threshold(y_validation, probability)
        metrics = calculate_metrics(y_validation, probability, threshold)
        validation_rows.append({"model": name, **metrics})
        fitted[name] = {"pipeline": pipeline, "threshold": threshold}

    comparison = pd.DataFrame(validation_rows).sort_values(
        ["pr_auc", "roc_auc"], ascending=False
    )
    comparison.to_csv(output / "validation_model_comparison.csv", index=False)
    print("\nValidation comparison")
    print(comparison[[
        "model", "roc_auc", "pr_auc", "threshold", "precision", "recall",
        "f1", "false_positives", "false_negatives"
    ]].to_string(index=False))

    champion_name = str(comparison.iloc[0]["model"])
    threshold = float(fitted[champion_name]["threshold"])
    print(f"\nSelected champion: {champion_name}")
    print(f"Validation-selected threshold: {threshold:.4f}")

    development = pd.concat([train, validation], ignore_index=True)
    X_development, y_development = development[features], development[TARGET]
    champion = Pipeline([
        ("preprocessor", make_preprocessor(numeric, categorical)),
        ("model", clone(model_specs[champion_name])),
    ])
    final_fit_parameters = {}
    if champion_name == "gradient_boosting":
        final_fit_parameters["model__sample_weight"] = compute_sample_weight(
            class_weight="balanced", y=y_development
        )
    champion.fit(X_development, y_development, **final_fit_parameters)

    test_probability = champion.predict_proba(X_test)[:, 1]
    test_metrics = calculate_metrics(y_test, test_probability, threshold)
    test_predictions = test[IDENTIFIERS + ["application_date", TARGET]].copy()
    test_predictions["predicted_probability"] = test_probability
    test_predictions["predicted_default"] = (test_probability >= threshold).astype(int)
    test_predictions.to_csv(output / "champion_test_predictions.csv", index=False)

    importance = permutation_importance(
        champion, X_test, y_test, scoring="average_precision",
        n_repeats=10, random_state=RANDOM_STATE, n_jobs=-1,
    )
    pd.DataFrame({
        "feature": features,
        "importance_mean": importance.importances_mean,
        "importance_std": importance.importances_std,
    }).sort_values("importance_mean", ascending=False).to_csv(
        output / "champion_permutation_importance.csv", index=False
    )

    metadata = {
        "model_name": champion_name,
        "model_version": "champion_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "selection_metric": "validation_pr_auc",
        "minimum_validation_recall": MINIMUM_RECALL,
        "decision_threshold": threshold,
        "train_rows": int(len(train)),
        "validation_rows": int(len(validation)),
        "test_rows": int(len(test)),
        "development_rows_for_final_fit": int(len(development)),
        "feature_columns": features,
        "numeric_columns": numeric,
        "categorical_columns": categorical,
        "validation_comparison": comparison.to_dict(orient="records"),
        "final_test_metrics": test_metrics,
        "scikit_learn_version": sklearn.__version__,
    }
    joblib.dump(champion, output / "champion_credit_risk_pipeline.joblib")
    (output / "champion_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    print("\nFinal champion test results")
    for key in ["roc_auc", "pr_auc", "precision", "recall", "f1", "accuracy", "brier_score"]:
        print(f"{key:12s}: {test_metrics[key]:.4f}")
    print(
        "Confusion    : "
        f"TN={test_metrics['true_negatives']}, FP={test_metrics['false_positives']}, "
        f"FN={test_metrics['false_negatives']}, TP={test_metrics['true_positives']}"
    )
    print(f"Artifacts    : {output}")


if __name__ == "__main__":
    main()