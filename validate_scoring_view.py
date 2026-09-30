from __future__ import annotations

import json
import os
from pathlib import Path

import joblib
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


PROJECT_ROOT = Path(__file__).resolve().parent
ARTIFACT_DIR = PROJECT_ROOT / "backend" / "ml" / "artifacts" / "model_comparison_v1"
MODEL_PATH = ARTIFACT_DIR / "champion_credit_risk_pipeline.joblib"
METADATA_PATH = ARTIFACT_DIR / "champion_metadata.json"
VIEW_NAME = "credit.ml_scoring_features_v1"
IDENTIFIERS = ["application_id", "customer_id", "application_date"]


def database_url() -> str:
    load_dotenv(PROJECT_ROOT / ".env")
    value = os.getenv("DATABASE_URL")
    if not value:
        raise RuntimeError("DATABASE_URL is missing from the project-root .env file")
    # SQLAlchemy + psycopg v3 driver.
    return value.replace("postgresql://", "postgresql+psycopg://", 1)


def metadata_feature_columns(metadata: dict) -> list[str]:
    for key in ("feature_columns", "features", "model_features"):
        value = metadata.get(key)
        if isinstance(value, list) and value:
            return value
    raise KeyError(
        "No feature list found in champion_metadata.json. "
        "Expected feature_columns, features, or model_features."
    )


def main() -> int:
    if not MODEL_PATH.exists() or not METADATA_PATH.exists():
        raise FileNotFoundError(f"Champion artifacts not found in {ARTIFACT_DIR}")

    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    expected = metadata_feature_columns(metadata)
    engine = create_engine(database_url())

    with engine.connect() as connection:
        columns = connection.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'credit'
                  AND table_name = 'ml_scoring_features_v1'
                ORDER BY ordinal_position
                """
            )
        ).scalars().all()

        if not columns:
            raise RuntimeError(
                "credit.ml_scoring_features_v1 does not exist. Run "
                "create_scoring_features_view.sql first."
            )

        actual = [name for name in columns if name not in IDENTIFIERS]
        missing = [name for name in expected if name not in actual]
        extra = [name for name in actual if name not in expected]
        order_ok = actual == expected

        print(f"View columns     : {len(columns)}")
        print(f"Expected features: {len(expected)}")
        print(f"Actual features  : {len(actual)}")
        print(f"Missing          : {missing or 'none'}")
        print(f"Extra            : {extra or 'none'}")
        print(f"Exact order      : {'yes' if order_ok else 'no'}")

        if missing or extra:
            raise RuntimeError("Scoring-view feature names do not match the model")

        # Select in the model's expected order even if PostgreSQL view order differs.
        select_columns = ", ".join(f'"{name}"' for name in expected)
        sample = pd.read_sql_query(
            text(f"SELECT {select_columns} FROM {VIEW_NAME} ORDER BY application_date DESC LIMIT 25"),
            connection,
        )
        counts = connection.execute(
            text(
                f"""
                SELECT COUNT(*) AS rows,
                       COUNT(DISTINCT application_id) AS applications
                FROM {VIEW_NAME}
                """
            )
        ).mappings().one()

    if sample.empty:
        raise RuntimeError("The scoring view exists but contains no rows")

    categorical = metadata.get("categorical_features", metadata.get("categorical_columns", []))
    for column in categorical:
        if column in sample.columns:
            sample[column] = sample[column].astype("string")

    pipeline = joblib.load(MODEL_PATH)
    probabilities = pipeline.predict_proba(sample[expected])[:, 1]
    if not pd.Series(probabilities).between(0, 1).all():
        raise RuntimeError("Model returned a probability outside [0, 1]")

    print(f"View rows        : {counts['rows']:,}")
    print(f"Unique apps      : {counts['applications']:,}")
    print(f"Scored sample    : {len(probabilities)}")
    print(f"Probability range: {probabilities.min():.4f} to {probabilities.max():.4f}")
    print("\nPASS: the live scoring view is compatible with the champion model.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
