from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path
from urllib.parse import quote_plus

import psycopg
from dotenv import load_dotenv
from psycopg import sql


# The order matters because of foreign-key relationships.
LOAD_PLAN = [
    ("security", "users", "users.csv"),
    ("banking", "customers", "customers.csv"),
    ("banking", "accounts", "accounts.csv"),
    ("banking", "account_transactions", "account_transactions.csv"),
    ("credit", "loan_applications", "loan_applications.csv"),
    ("banking", "credit_bureau_reports", "credit_bureau_reports.csv"),
    ("credit", "credit_assessments", "credit_assessments.csv"),
    ("credit", "credit_decisions", "credit_decisions.csv"),
    ("banking", "loans", "loans.csv"),
    ("banking", "repayment_schedule", "repayment_schedule.csv"),
    ("banking", "loan_payments", "loan_payments.csv"),
    ("credit", "risk_alerts", "risk_alerts.csv"),
    ("security", "audit_logs", "audit_logs.csv"),
]


def project_root() -> Path:
    """Supports placement in database/loaders or directly in the project root."""
    script = Path(__file__).resolve()
    if script.parent.name == "loaders" and script.parent.parent.name == "database":
        return script.parents[2]
    return script.parent


def connection_string() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        # SQLAlchemy URLs contain a driver suffix that psycopg doesn't accept.
        return url.replace("postgresql+psycopg://", "postgresql://", 1)

    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    database = os.getenv("DB_NAME", "msme_credit_db")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")

    if not password:
        raise RuntimeError(
            "Database configuration missing. Set DATABASE_URL or DB_PASSWORD in .env."
        )

    return (
        f"postgresql://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{database}"
    )


def read_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError(f"CSV is empty: {path}") from exc

    header = [column.strip() for column in header]
    if not header or any(not column for column in header):
        raise ValueError(f"CSV has an invalid header: {path}")
    if len(header) != len(set(header)):
        raise ValueError(f"CSV has duplicate columns: {path}")
    return header


def validate_files(csv_dir: Path) -> dict[str, list[str]]:
    headers: dict[str, list[str]] = {}
    problems: list[str] = []

    for _, _, filename in LOAD_PLAN:
        path = csv_dir / filename
        if not path.is_file():
            problems.append(f"Missing file: {path}")
            continue
        try:
            headers[filename] = read_header(path)
        except ValueError as exc:
            problems.append(str(exc))

    if problems:
        raise RuntimeError("CSV validation failed:\n  - " + "\n  - ".join(problems))
    return headers


def database_columns(cursor, schema: str, table: str) -> list[str]:
    cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = %s
          AND table_name = %s
        ORDER BY ordinal_position
        """,
        (schema, table),
    )
    return [row[0] for row in cursor.fetchall()]


def validate_headers(cursor, headers: dict[str, list[str]]) -> None:
    problems: list[str] = []

    for schema, table, filename in LOAD_PLAN:
        table_columns = database_columns(cursor, schema, table)
        if not table_columns:
            problems.append(f"Table does not exist: {schema}.{table}")
            continue

        csv_columns = headers[filename]
        unknown = [column for column in csv_columns if column not in table_columns]
        if unknown:
            problems.append(
                f"{filename} has columns not found in {schema}.{table}: "
                + ", ".join(unknown)
            )

    if problems:
        raise RuntimeError("CSV/database header validation failed:\n  - " + "\n  - ".join(problems))


def truncate_target_tables(cursor) -> None:
    targets = [sql.Identifier(schema, table) for schema, table, _ in LOAD_PLAN]
    statement = sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE").format(
        sql.SQL(", ").join(targets)
    )
    cursor.execute(statement)


def load_csv(cursor, schema: str, table: str, path: Path, columns: list[str]) -> None:
    copy_statement = sql.SQL(
        "COPY {} ({}) FROM STDIN WITH "
        "(FORMAT CSV, HEADER TRUE, NULL '', ENCODING 'UTF8')"
    ).format(
        sql.Identifier(schema, table),
        sql.SQL(", ").join(sql.Identifier(column) for column in columns),
    )

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        with cursor.copy(copy_statement) as copy:
            while chunk := handle.read(1024 * 1024):
                copy.write(chunk)


def count_rows(cursor, schema: str, table: str) -> int:
    cursor.execute(
        sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(schema, table))
    )
    return cursor.fetchone()[0]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Replace old MSME synthetic rows and load regenerated CSV files."
    )
    parser.add_argument(
        "--csv-dir",
        type=Path,
        help="CSV directory. Defaults to <project-root>/data/generated.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirm replacement without an interactive prompt.",
    )
    args = parser.parse_args()

    root = project_root()
    load_dotenv(root / ".env")
    csv_dir = (args.csv_dir or root / "data" / "generated").resolve()

    print(f"Project root : {root}")
    print(f"CSV directory: {csv_dir}")
    print("Validating CSV files...")
    headers = validate_files(csv_dir)

    if not args.yes:
        answer = input(
            "This will replace all rows in the 13 synthetic-data tables. "
            "Type REPLACE to continue: "
        )
        if answer.strip() != "REPLACE":
            print("Cancelled. The database was not changed.")
            return 0

    try:
        with psycopg.connect(connection_string()) as connection:
            # The whole operation is one transaction. Any exception causes rollback.
            with connection.transaction():
                with connection.cursor() as cursor:
                    print("Validating CSV headers against PostgreSQL...")
                    validate_headers(cursor, headers)

                    print("Truncating old synthetic rows...")
                    truncate_target_tables(cursor)

                    for schema, table, filename in LOAD_PLAN:
                        path = csv_dir / filename
                        print(f"Loading {schema}.{table} from {filename}...", end=" ")
                        load_csv(cursor, schema, table, path, headers[filename])
                        rows = count_rows(cursor, schema, table)
                        print(f"{rows:,} rows")

            print("\nLoad completed successfully. Transaction committed.")
            return 0

    except Exception as exc:
        print("\nLOAD FAILED. PostgreSQL rolled back the transaction.", file=sys.stderr)
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())