from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


def find_project_root() -> Path:
    script = Path(__file__).resolve()
    for candidate in [script.parent, *script.parents]:
        if (candidate / ".env").exists():
            return candidate
    # Expected placement: <project>/backend/ml/build_training_dataset.py
    return script.parents[2]


def database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url

    password = os.getenv("DB_PASSWORD", "")
    if not password:
        raise RuntimeError(
            "Set DATABASE_URL or DB_PASSWORD in the project .env file."
        )

    user = os.getenv("DB_USER", "postgres")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "msme_credit_db")
    return (
        f"postgresql+psycopg://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{name}"
    )


def main() -> None:
    root = find_project_root()
    load_dotenv(root / ".env")

    output_dir = root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset_path = output_dir / "credit_risk_training_dataset.csv"
    report_path = output_dir / "training_dataset_quality_report.json"

    print(f"Project root : {root}")
    print("Reading credit.ml_training_dataset_v1...")

    engine = create_engine(database_url(), pool_pre_ping=True)
    query = text(
        """
        SELECT *
        FROM credit.ml_training_dataset_v1
        ORDER BY application_date, application_id
        """
    )

    try:
        with engine.connect() as connection:
            data = pd.read_sql_query(query, connection)
    finally:
        engine.dispose()

    if data.empty:
        raise RuntimeError("The training view returned zero rows.")

    required_columns = {
        "loan_id",
        "application_id",
        "customer_id",
        "application_date",
        "default_12m",
        "max_dpd_first_12m",
    }
    missing_required = sorted(required_columns - set(data.columns))
    if missing_required:
        raise RuntimeError(
            "Training view is missing required columns: "
            + ", ".join(missing_required)
        )

    data["application_date"] = pd.to_datetime(
        data["application_date"], errors="raise"
    )
    data["default_12m"] = pd.to_numeric(
        data["default_12m"], errors="raise"
    ).astype("int8")

    invalid_targets = sorted(set(data["default_12m"].unique()) - {0, 1})
    if invalid_targets:
        raise RuntimeError(f"Invalid target values: {invalid_targets}")

    duplicate_loans = int(data["loan_id"].duplicated().sum())
    duplicate_applications = int(data["application_id"].duplicated().sum())
    if duplicate_loans or duplicate_applications:
        raise RuntimeError(
            "Duplicate training records detected: "
            f"loan_id={duplicate_loans}, application_id={duplicate_applications}"
        )

    # max_dpd_first_12m is used to construct the target and must never be a feature.
    model_data = data.drop(columns=["max_dpd_first_12m"])

    numeric_columns = model_data.select_dtypes(include=["number"]).columns
    infinity_count = int(
        np.isinf(model_data[numeric_columns].astype(float)).sum().sum()
    )
    if infinity_count:
        model_data[numeric_columns] = model_data[numeric_columns].replace(
            [np.inf, -np.inf], np.nan
        )

    rows = len(model_data)
    defaults = int(model_data["default_12m"].sum())
    non_defaults = rows - defaults
    default_rate = defaults / rows

    if rows < 500:
        raise RuntimeError(f"Too few training rows: {rows}")
    if defaults < 30:
        raise RuntimeError(f"Too few default cases: {defaults}")

    missing_values = {
        column: int(count)
        for column, count in model_data.isna().sum().items()
        if int(count) > 0
    }

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "credit.ml_training_dataset_v1",
        "output_file": str(dataset_path),
        "rows": rows,
        "columns": len(model_data.columns),
        "unique_customers": int(model_data["customer_id"].nunique()),
        "defaults": defaults,
        "non_defaults": non_defaults,
        "default_rate": round(default_rate, 6),
        "first_application_date": model_data["application_date"].min().date().isoformat(),
        "last_application_date": model_data["application_date"].max().date().isoformat(),
        "duplicate_loan_ids": duplicate_loans,
        "duplicate_application_ids": duplicate_applications,
        "infinite_numeric_values_replaced": infinity_count,
        "missing_values_by_column": missing_values,
        "excluded_leakage_columns": ["max_dpd_first_12m"],
        "identifier_columns_not_for_modeling": [
            "loan_id",
            "application_id",
            "customer_id",
        ],
        "target_column": "default_12m",
    }

    model_data.to_csv(dataset_path, index=False, encoding="utf-8")
    report_path.write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    print("\nTraining dataset created successfully")
    print(f"Rows             : {rows:,}")
    print(f"Columns          : {len(model_data.columns):,}")
    print(f"Unique customers : {report['unique_customers']:,}")
    print(f"Defaults         : {defaults:,}")
    print(f"Non-defaults     : {non_defaults:,}")
    print(f"Default rate     : {default_rate:.2%}")
    print(f"Missing columns  : {len(missing_values):,}")
    print(f"Dataset          : {dataset_path}")
    print(f"Quality report   : {report_path}")


if __name__ == "__main__":
    main()