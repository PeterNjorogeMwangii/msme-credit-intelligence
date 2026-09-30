from __future__ import annotations

import argparse
import csv
import os
import shutil
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


CENT = Decimal("0.01")


def cash(value: str | None) -> Decimal:
    return Decimal(value or "0").quantize(CENT, rounding=ROUND_HALF_UP)


def text_amount(value: Decimal) -> str:
    return f"{value.quantize(CENT, rounding=ROUND_HALF_UP):.2f}"


def transform(filename: str, row: dict[str, str]) -> bool:
    original = row.copy()

    if filename == "customers.csv":
        row["kyc_status"] = {"VALID": "VERIFIED"}.get(
            row.get("kyc_status", ""), row.get("kyc_status", "")
        )
        row["business_type"] = {"SOLE_PROPRIETOR": "SOLE_PROPRIETORSHIP"}.get(
            row.get("business_type", ""), row.get("business_type", "")
        )

    elif filename == "account_transactions.csv":
        category = row.get("transaction_category", "")
        if category == "CASH":
            row["transaction_category"] = (
                "CASH_DEPOSIT"
                if row.get("credit_debit_indicator") == "C"
                else "CASH_WITHDRAWAL"
            )
        else:
            row["transaction_category"] = {
                "SALES": "CUSTOMER_REVENUE",
                "TRANSFER": "OWN_ACCOUNT_TRANSFER",
                "SUPPLIER": "SUPPLIER_PAYMENT",
                "PAYROLL": "SALARY_PAYMENT",
            }.get(category, category)
        row["channel_code"] = {
            "CARD": "POS",
        }.get(row.get("channel_code", ""), row.get("channel_code", ""))

    elif filename == "loan_applications.csv":
        row["application_channel"] = {
            "ONLINE": "WEB",
            "RM": "RELATIONSHIP_MANAGER",
        }.get(
            row.get("application_channel", ""),
            row.get("application_channel", ""),
        )

    elif filename == "loan_payments.csv":
        row["payment_channel"] = {
            "MPESA": "MOBILE_MONEY",
            "BRANCH": "CASH",
        }.get(row.get("payment_channel", ""), row.get("payment_channel", ""))

        # Enforce payment_amount = principal + interest + fees + penalty exactly.
        total = cash(row.get("payment_amount"))
        principal = min(cash(row.get("principal_paid")), total)
        fees = max(Decimal("0.00"), cash(row.get("fees_paid")))
        penalty = max(Decimal("0.00"), cash(row.get("penalty_paid")))
        if principal + fees + penalty > total:
            principal, fees, penalty = total, Decimal("0.00"), Decimal("0.00")
        interest = total - principal - fees - penalty
        row["payment_amount"] = text_amount(total)
        row["principal_paid"] = text_amount(principal)
        row["interest_paid"] = text_amount(interest)
        row["fees_paid"] = text_amount(fees)
        row["penalty_paid"] = text_amount(penalty)

    elif filename == "repayment_schedule.csv":
        row["schedule_status"] = {
            "FUTURE": "PENDING",
        }.get(row.get("schedule_status", ""), row.get("schedule_status", ""))

        # Enforce total and outstanding check constraints exactly after rounding.
        principal = cash(row.get("principal_due"))
        interest = cash(row.get("interest_due"))
        fees = cash(row.get("fees_due"))
        total = principal + interest + fees
        paid = min(max(Decimal("0.00"), cash(row.get("amount_paid"))), total)
        outstanding = total - paid
        row["principal_due"] = text_amount(principal)
        row["interest_due"] = text_amount(interest)
        row["fees_due"] = text_amount(fees)
        row["total_amount_due"] = text_amount(total)
        row["amount_paid"] = text_amount(paid)
        row["outstanding_amount"] = text_amount(outstanding)

    elif filename == "credit_assessments.csv":
        recommendation = row.get("system_recommendation", "")
        row["system_recommendation"] = {
            "APPROVE": "RECOMMEND_APPROVAL",
            "DECLINE": "RECOMMEND_DECLINE",
        }.get(recommendation, recommendation)

    elif filename == "credit_decisions.csv":
        decision = row.get("decision_type", "")
        row["decision_type"] = {
            "APPROVE": "APPROVED",
            "DECLINE": "DECLINED",
        }.get(decision, decision)

    elif filename == "risk_alerts.csv":
        row["alert_type"] = {
            "DELINQUENCY": "PAYMENT_OVERDUE",
        }.get(row.get("alert_type", ""), row.get("alert_type", ""))

    return row != original


def process(path: Path, backup_dir: Path) -> tuple[int, int]:
    temporary = path.with_suffix(path.suffix + ".tmp")
    backup = backup_dir / path.name
    shutil.copy2(path, backup)

    rows = 0
    changed = 0
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            if not reader.fieldnames:
                raise ValueError(f"Missing CSV header: {path}")
            with temporary.open("w", encoding="utf-8", newline="") as target:
                writer = csv.DictWriter(target, fieldnames=reader.fieldnames)
                writer.writeheader()
                for row in reader:
                    rows += 1
                    if transform(path.name, row):
                        changed += 1
                    writer.writerow(row)
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return rows, changed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Make generated MSME CSV values comply with PostgreSQL checks."
    )
    parser.add_argument(
        "--csv-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "data" / "generated",
    )
    args = parser.parse_args()
    csv_dir = args.csv_dir.resolve()
    if not csv_dir.is_dir():
        raise FileNotFoundError(f"CSV directory not found: {csv_dir}")

    targets = [
        "customers.csv",
        "account_transactions.csv",
        "loan_applications.csv",
        "loan_payments.csv",
        "repayment_schedule.csv",
        "credit_assessments.csv",
        "credit_decisions.csv",
        "risk_alerts.csv",
    ]
    missing = [name for name in targets if not (csv_dir / name).is_file()]
    if missing:
        raise FileNotFoundError("Missing files: " + ", ".join(missing))

    backup_dir = csv_dir / "before_constraint_fix"
    backup_dir.mkdir(exist_ok=True)
    print(f"CSV directory : {csv_dir}")
    print(f"Backup folder : {backup_dir}")
    for filename in targets:
        rows, changed = process(csv_dir / filename, backup_dir)
        print(f"{filename:32s} rows={rows:>9,} changed={changed:>9,}")
    print("Constraint corrections completed successfully.")


if __name__ == "__main__":
    main()