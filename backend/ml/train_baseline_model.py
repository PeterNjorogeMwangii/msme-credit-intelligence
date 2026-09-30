from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.calibration import calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    classification_report,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


RANDOM_STATE = 42
TEST_SIZE = 0.20
THRESHOLD = 0.50
TARGET = "default_12m"
IDENTIFIERS = ["loan_id", "application_id", "customer_id"]
DROP_FROM_MODEL = IDENTIFIERS + ["application_date", TARGET]


def find_project_root() -> Path:
    script = Path(__file__).resolve()
    for candidate in [script.parent, *script.parents]:
        if (candidate / ".env").exists():
            return candidate
    return script.parents[2]


def make_one_hot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=True)
    except TypeError:  # scikit-learn earlier than 1.2
        return OneHotEncoder(handle_unknown="ignore", sparse=True)


def save_target_chart(data: pd.DataFrame, path: Path) -> None:
    counts = data[TARGET].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(["Non-default", "Default"], counts.values, color=["#2563eb", "#dc2626"])
    ax.set_title("12-Month Default Target Distribution")
    ax.set_ylabel("Applications")
    for bar, value in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width()/2, value, f"{value:,}", ha="center", va="bottom")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def save_eda_tables(data: pd.DataFrame, numeric: list[str], categorical: list[str], output: Path) -> None:
    numeric_rows = []
    for column in numeric:
        numeric_rows.append({
            "feature": column,
            "missing": int(data[column].isna().sum()),
            "overall_mean": data[column].mean(),
            "non_default_mean": data.loc[data[TARGET] == 0, column].mean(),
            "default_mean": data.loc[data[TARGET] == 1, column].mean(),
            "overall_median": data[column].median(),
            "minimum": data[column].min(),
            "maximum": data[column].max(),
        })
    pd.DataFrame(numeric_rows).to_csv(output / "numeric_feature_summary.csv", index=False)

    categorical_rows = []
    for column in categorical:
        grouped = (
            data.assign(**{column: data[column].astype("string").fillna("MISSING")})
            .groupby(column, dropna=False)[TARGET]
            .agg(["count", "sum", "mean"])
            .reset_index()
        )
        for _, row in grouped.iterrows():
            categorical_rows.append({
                "feature": column,
                "category": row[column],
                "applications": int(row["count"]),
                "defaults": int(row["sum"]),
                "default_rate": float(row["mean"]),
            })
    pd.DataFrame(categorical_rows).to_csv(output / "categorical_default_rates.csv", index=False)


def main() -> None:
    root = find_project_root()
    dataset_path = root / "data" / "processed" / "credit_risk_training_dataset.csv"
    artifact_dir = root / "backend" / "ml" / "artifacts" / "baseline_v1"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    if not dataset_path.is_file():
        raise FileNotFoundError(f"Training dataset not found: {dataset_path}")

    data = pd.read_csv(dataset_path, parse_dates=["application_date"])
    required = set(DROP_FROM_MODEL)
    missing = sorted(required - set(data.columns))
    if missing:
        raise RuntimeError("Missing required columns: " + ", ".join(missing))

    # County codes are categories even when pandas infers them as integers.
    data["county_code"] = data["county_code"].astype("string")
    data["adverse_listing_flag"] = data["adverse_listing_flag"].astype("string")

    feature_columns = [column for column in data.columns if column not in DROP_FROM_MODEL]
    categorical_columns = data[feature_columns].select_dtypes(include=["object", "string", "category", "bool"]).columns.tolist()
    numeric_columns = [column for column in feature_columns if column not in categorical_columns]

    # Split unique customers first so one business never appears in both sets.
    customer_targets = data.groupby("customer_id", as_index=False)[TARGET].max()
    train_customers, test_customers = train_test_split(
        customer_targets,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=customer_targets[TARGET],
    )
    train_ids = set(train_customers["customer_id"])
    test_ids = set(test_customers["customer_id"])
    if train_ids & test_ids:
        raise RuntimeError("Customer leakage detected between train and test sets.")

    train = data[data["customer_id"].isin(train_ids)].copy()
    test = data[data["customer_id"].isin(test_ids)].copy()
    X_train, y_train = train[feature_columns], train[TARGET]
    X_test, y_test = test[feature_columns], test[TARGET]

    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", make_one_hot_encoder()),
    ])
    preprocessor = ColumnTransformer([
        ("numeric", numeric_pipeline, numeric_columns),
        ("categorical", categorical_pipeline, categorical_columns),
    ])
    model = LogisticRegression(
        class_weight="balanced",
        max_iter=3000,
        solver="liblinear",
        random_state=RANDOM_STATE,
    )
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", model),
    ])

    print(f"Training rows : {len(train):,} ({int(y_train.sum()):,} defaults)")
    print(f"Test rows     : {len(test):,} ({int(y_test.sum()):,} defaults)")
    print(f"Numeric       : {len(numeric_columns)} features")
    print(f"Categorical   : {len(categorical_columns)} features")
    print("Training logistic-regression baseline...")
    pipeline.fit(X_train, y_train)

    probabilities = pipeline.predict_proba(X_test)[:, 1]
    predictions = (probabilities >= THRESHOLD).astype(int)
    matrix = confusion_matrix(y_test, predictions)
    tn, fp, fn, tp = matrix.ravel()
    metrics = {
        "roc_auc": float(roc_auc_score(y_test, probabilities)),
        "pr_auc": float(average_precision_score(y_test, probabilities)),
        "accuracy": float(accuracy_score(y_test, predictions)),
        "precision": float(precision_score(y_test, predictions, zero_division=0)),
        "recall": float(recall_score(y_test, predictions, zero_division=0)),
        "f1": float(f1_score(y_test, predictions, zero_division=0)),
        "brier_score": float(brier_score_loss(y_test, probabilities)),
        "log_loss": float(log_loss(y_test, probabilities)),
        "true_negatives": int(tn), "false_positives": int(fp),
        "false_negatives": int(fn), "true_positives": int(tp),
    }

    save_target_chart(data, artifact_dir / "target_distribution.png")
    save_eda_tables(data, numeric_columns, categorical_columns, artifact_dir)

    fpr, tpr, _ = roc_curve(y_test, probabilities)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(fpr, tpr, label=f"ROC-AUC = {metrics['roc_auc']:.3f}")
    ax.plot([0, 1], [0, 1], "--", color="gray")
    ax.set(xlabel="False Positive Rate", ylabel="True Positive Rate", title="Baseline ROC Curve")
    ax.legend(); fig.tight_layout(); fig.savefig(artifact_dir / "roc_curve.png", dpi=160); plt.close(fig)

    precision, recall, _ = precision_recall_curve(y_test, probabilities)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(recall, precision, label=f"PR-AUC = {metrics['pr_auc']:.3f}")
    ax.axhline(y_test.mean(), linestyle="--", color="gray", label="Default prevalence")
    ax.set(xlabel="Recall", ylabel="Precision", title="Precision-Recall Curve")
    ax.legend(); fig.tight_layout(); fig.savefig(artifact_dir / "precision_recall_curve.png", dpi=160); plt.close(fig)

    observed, predicted = calibration_curve(y_test, probabilities, n_bins=8, strategy="quantile")
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(predicted, observed, marker="o", label="Model")
    ax.plot([0, 1], [0, 1], "--", color="gray", label="Perfect calibration")
    ax.set(xlabel="Mean predicted probability", ylabel="Observed default rate", title="Calibration Curve")
    ax.legend(); fig.tight_layout(); fig.savefig(artifact_dir / "calibration_curve.png", dpi=160); plt.close(fig)

    fig, ax = plt.subplots(figsize=(5, 4))
    image = ax.imshow(matrix, cmap="Blues")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(matrix[i, j]), ha="center", va="center")
    ax.set_xticks([0, 1], ["Non-default", "Default"]); ax.set_yticks([0, 1], ["Non-default", "Default"])
    ax.set(xlabel="Predicted", ylabel="Actual", title=f"Confusion Matrix at {THRESHOLD:.2f}")
    fig.colorbar(image, ax=ax); fig.tight_layout(); fig.savefig(artifact_dir / "confusion_matrix.png", dpi=160); plt.close(fig)

    transformed_names = pipeline.named_steps["preprocessor"].get_feature_names_out()
    coefficients = pipeline.named_steps["model"].coef_[0]
    coefficient_table = pd.DataFrame({"feature": transformed_names, "coefficient": coefficients})
    coefficient_table["absolute_coefficient"] = coefficient_table["coefficient"].abs()
    coefficient_table.sort_values("absolute_coefficient", ascending=False).to_csv(
        artifact_dir / "model_coefficients.csv", index=False
    )

    prediction_output = test[IDENTIFIERS + ["application_date", TARGET]].copy()
    prediction_output["predicted_probability"] = probabilities
    prediction_output["predicted_default"] = predictions
    prediction_output.to_csv(artifact_dir / "test_predictions.csv", index=False)

    metadata = {
        "model_name": "msme_default_12m_logistic_regression",
        "model_version": "baseline_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "random_state": RANDOM_STATE,
        "test_size": TEST_SIZE,
        "decision_threshold": THRESHOLD,
        "target": TARGET,
        "training_rows": int(len(train)),
        "test_rows": int(len(test)),
        "training_defaults": int(y_train.sum()),
        "test_defaults": int(y_test.sum()),
        "feature_columns": feature_columns,
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "identifier_columns": IDENTIFIERS,
        "metrics": metrics,
        "classification_report": classification_report(y_test, predictions, output_dict=True, zero_division=0),
        "python_packages": {
            "pandas": pd.__version__, "numpy": np.__version__, "scikit_learn": sklearn.__version__,
        },
    }
    joblib.dump(pipeline, artifact_dir / "credit_risk_pipeline.joblib")
    (artifact_dir / "model_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print("\nBaseline evaluation")
    for name in ["roc_auc", "pr_auc", "precision", "recall", "f1", "accuracy", "brier_score"]:
        print(f"{name:12s}: {metrics[name]:.4f}")
    print(f"Confusion    : TN={tn}, FP={fp}, FN={fn}, TP={tp}")
    print(f"Artifacts    : {artifact_dir}")


if __name__ == "__main__":
    main()