from __future__ import annotations

import argparse
import csv
import json
import math
import random
import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

SEED = 20260921
SNAPSHOT = date(2026, 9, 18)
CUSTOMERS = 5000
APPLICATIONS = 5500
TX_COUNT = 400000
HISTORICAL_END = date(2025, 8, 31)

OUT = Path(__file__).resolve().parents[2] / "data" / "generated"


def iso_ts(d: date, hour: int = 10) -> str:
    return datetime(d.year, d.month, d.day, hour, 0, tzinfo=timezone.utc).isoformat()


def between(a: date, b: date) -> date:
    return a + timedelta(days=random.randint(0, max(0, (b - a).days)))


def money(x: float) -> str:
    return f"{max(0, x):.2f}"


def write_csv(name: str, fields: list[str], rows: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"{name:32s} {len(rows):>9,}")


def weighted(items):
    values, weights = zip(*items)
    return random.choices(values, weights=weights, k=1)[0]


def main() -> None:
    random.seed(SEED)
    sectors = [
        ("G47", "Retail trade", 30), ("C10", "Food manufacturing", 12),
        ("A01", "Agriculture", 16), ("H49", "Transport", 12),
        ("I56", "Food services", 10), ("F41", "Construction", 8),
        ("J62", "Information technology", 6), ("S96", "Personal services", 6),
    ]
    counties = ["001", "003", "022", "025", "027", "030", "032", "037", "040", "047"]
    customers, accounts = [], []
    customer_meta = {}

    for i in range(1, CUSTOMERS + 1):
        cid = f"C{i:06d}"
        industry, description, sector_risk = random.choice(sectors)
        incorporation = between(date(2000, 1, 1), date(2022, 12, 31))
        relationship = between(max(incorporation, date(2012, 1, 1)), date(2022, 6, 30))
        turnover = round(math.exp(random.uniform(math.log(1_000_000), math.log(180_000_000))), 2)
        employees = max(1, int(turnover / random.uniform(1_500_000, 5_000_000)))
        latent = min(0.98, max(0.02, random.betavariate(2.2, 5.5) + sector_risk / 200))
        customer_meta[cid] = {"risk": latent, "turnover": turnover, "relationship": relationship}
        customers.append({
            "customer_id": cid, "customer_number": f"MSME{i:07d}", "customer_type": "BUSINESS",
            "legal_name": f"Enterprise {i:05d} Limited", "trading_name": f"Enterprise {i:05d}",
            "registration_number": f"CPR/{2010 + i % 16}/{i:06d}", "tax_identifier": f"P{i:09d}",
            "business_type": weighted([("LIMITED_COMPANY", 50), ("SOLE_PROPRIETOR", 35), ("PARTNERSHIP", 15)]),
            "industry_code": industry, "industry_description": description,
            "incorporation_date": incorporation.isoformat(), "relationship_start_date": relationship.isoformat(),
            "employee_count": employees, "annual_turnover_declared": money(turnover), "turnover_currency": "KES",
            "county_code": random.choice(counties), "branch_code": f"BR{random.randint(1, 25):03d}",
            "relationship_manager_id": "", "kyc_status": "VALID", "kyc_review_date": between(date(2025, 1, 1), SNAPSHOT).isoformat(),
            "aml_risk_classification": weighted([("LOW", 65), ("MEDIUM", 30), ("HIGH", 5)]),
            "pep_flag": random.random() < .01, "sanctions_match_flag": False, "record_status": "ACTIVE",
            "created_at": iso_ts(relationship), "updated_at": iso_ts(SNAPSHOT),
        })
        for n in range(1 if random.random() < .62 else 2):
            aid = f"A{len(accounts)+1:07d}"
            accounts.append({
                "account_id": aid, "account_number_token": f"TOK-{uuid.uuid4().hex[:20]}", "customer_id": cid,
                "product_code": "CUR001" if n == 0 else "SAV001", "product_name": "Business Current" if n == 0 else "Business Savings",
                "account_type": "CURRENT" if n == 0 else "SAVINGS", "currency_code": "KES", "branch_code": customers[-1]["branch_code"],
                "open_date": relationship.isoformat(), "close_date": "", "account_status": "ACTIVE",
                "ledger_balance": money(turnover * random.uniform(.005, .08)), "available_balance": money(turnover * random.uniform(.004, .07)),
                "overdraft_limit": money(turnover * random.uniform(0, .03)), "uncleared_balance": "0.00",
                "last_credit_date": SNAPSHOT.isoformat(), "last_debit_date": SNAPSHOT.isoformat(), "dormancy_flag": False,
                "freeze_code": "", "created_at": iso_ts(relationship), "updated_at": iso_ts(SNAPSHOT),
            })

    # Application dates: 75% mature historical cohort, 25% recent operational cohort.
    app_customers = list(customer_meta) + random.sample(list(customer_meta), APPLICATIONS - CUSTOMERS)
    random.shuffle(app_customers)
    applications, bureaus, app_meta = [], [], {}
    for i, cid in enumerate(app_customers, 1):
        historical = i <= round(APPLICATIONS * .75)
        app_date = between(date(2023, 1, 1), HISTORICAL_END) if historical else between(date(2025, 9, 1), SNAPSHOT - timedelta(days=30))
        cm = customer_meta[cid]
        risk = cm["risk"]
        bureau_score = int(max(300, min(850, 830 - risk * 470 + random.gauss(0, 35))))
        monthly_revenue = cm["turnover"] / 12 * random.uniform(.75, 1.2)
        monthly_expenses = monthly_revenue * random.uniform(.45 + risk * .2, .82)
        existing_debt = monthly_revenue * random.uniform(0, .08 + risk * .2)
        requested = min(cm["turnover"] * random.uniform(.04, .35), 25_000_000)
        approval_probability = max(.12, min(.72, .68 - risk * .65 + (bureau_score - 550) / 900))
        approved = random.random() < approval_probability
        appid = f"APP{i:07d}"
        status = "APPROVED" if approved else "DECLINED"
        purpose = random.choice(["WORKING_CAPITAL", "ASSET_FINANCE", "INVENTORY", "EXPANSION", "TRADE_FINANCE"])
        term = random.choice([6, 9, 12, 18, 24, 36])
        applications.append({
            "application_id": appid, "customer_id": cid, "application_date": app_date.isoformat(),
            "application_channel": random.choice(["BRANCH", "ONLINE", "RM", "MOBILE"]), "loan_product_code": "MSME_TERM",
            "loan_purpose_code": purpose, "loan_purpose_description": purpose.replace("_", " ").title(),
            "requested_amount": money(requested), "requested_currency": "KES", "requested_term_months": term,
            "declared_monthly_revenue": money(monthly_revenue), "declared_monthly_expenses": money(monthly_expenses),
            "existing_monthly_debt": money(existing_debt), "collateral_type": random.choice(["PROPERTY", "VEHICLE", "DEPOSIT", "NONE"]),
            "collateral_value": money(requested * random.uniform(0, 1.8)), "application_status": status,
            "assigned_analyst_id": "", "submitted_at": iso_ts(app_date), "created_at": iso_ts(app_date), "updated_at": iso_ts(app_date),
        })
        bureau_id = f"CRB{i:07d}"
        bureaus.append({
            "bureau_report_id": bureau_id, "customer_id": cid, "application_id": appid, "report_date": app_date.isoformat(),
            "bureau_provider": random.choice(["TRANSUNION", "METROPOL", "CREDITINFO"]), "bureau_score": bureau_score,
            "total_active_facilities": max(0, int(random.gauss(1 + risk * 4, 1))), "total_closed_facilities": random.randint(0, 8),
            "total_outstanding_balance": money(existing_debt * random.uniform(8, 24)), "total_monthly_obligation": money(existing_debt),
            "secured_facilities": random.randint(0, 2), "unsecured_facilities": random.randint(0, 4),
            "max_days_past_due_12m": weighted([(0, 60), (15, 12), (30, 12), (60, 8), (90, 8)]) if risk > .45 else weighted([(0, 88), (15, 8), (30, 4)]),
            "delinquent_facilities": 1 if risk > .65 and random.random() < .55 else 0, "written_off_facilities": 1 if risk > .82 and random.random() < .2 else 0,
            "legal_cases": 1 if risk > .88 and random.random() < .15 else 0, "credit_enquiries_3m": random.randint(0, 4),
            "credit_enquiries_6m": random.randint(0, 7), "oldest_facility_date": between(date(2012, 1, 1), app_date).isoformat(),
            "adverse_listing_flag": risk > .78 and random.random() < .55, "report_reference": f"REF-{uuid.uuid4().hex[:16].upper()}",
            "created_at": iso_ts(app_date),
        })
        app_meta[appid] = {"cid": cid, "date": app_date, "risk": risk, "approved": approved, "historical": historical,
                           "amount": requested, "term": term, "revenue": monthly_revenue, "expenses": monthly_expenses,
                           "debt": existing_debt, "bureau_score": bureau_score}

    approved_historical = [a for a, m in app_meta.items() if m["approved"] and m["historical"]]
    default_count = round(len(approved_historical) * .12)
    default_apps = set(random.choices(approved_historical, weights=[app_meta[a]["risk"] ** 2 + .03 for a in approved_historical], k=default_count * 3))
    if len(default_apps) < default_count:
        remaining = sorted((a for a in approved_historical if a not in default_apps), key=lambda a: app_meta[a]["risk"], reverse=True)
        default_apps.update(remaining[:default_count-len(default_apps)])
    elif len(default_apps) > default_count:
        default_apps = set(sorted(default_apps, key=lambda a: app_meta[a]["risk"], reverse=True)[:default_count])

    primary_account = {}
    for account in accounts:
        primary_account.setdefault(account["customer_id"], account["account_id"])
    loans, schedules, payments = [], [], []
    loan_num = schedule_num = payment_num = 0
    for appid, m in app_meta.items():
        if not m["approved"]:
            continue
        loan_num += 1
        lid = f"L{loan_num:07d}"
        disb = m["date"] + timedelta(days=random.randint(1, 10))
        term = m["term"]
        principal = m["amount"] * random.uniform(.72, 1.0)
        rate = random.uniform(.13, .22)
        installment = principal * (1 + rate * term / 12) / term
        is_default = appid in default_apps
        if is_default:
            classification = "LOSS"; status = "IN_ARREARS"; current_dpd = random.randint(90, 210)
        elif m["risk"] > .68 and random.random() < .35:
            classification = random.choice(["WATCH", "SUBSTANDARD", "DOUBTFUL"]); status = "IN_ARREARS"
            current_dpd = {"WATCH": 20, "SUBSTANDARD": 55, "DOUBTFUL": 75}[classification]
        else:
            classification = "PERFORMING"; current_dpd = 0
            status = "SETTLED" if disb + timedelta(days=term * 30) < SNAPSHOT and random.random() < .75 else "ACTIVE"
        writeoff = is_default and random.random() < .28
        paid_installments = 0
        for k in range(1, term + 1):
            due = disb + timedelta(days=30 * k)
            if due > SNAPSHOT:
                sched_status, amount_paid, dpd, settlement = "FUTURE", 0, 0, ""
            elif is_default and k >= max(2, term // 3):
                dpd = min(210, 90 + (k - max(2, term // 3)) * 15)
                sched_status, amount_paid, settlement = "OVERDUE", installment * random.uniform(0, .25), ""
            elif classification != "PERFORMING" and k >= max(2, term // 2):
                dpd = current_dpd; sched_status, amount_paid, settlement = "OVERDUE", installment * random.uniform(.3, .8), ""
            else:
                dpd = 0; sched_status, amount_paid = "PAID", installment
                settlement = (due + timedelta(days=random.randint(-3, 5))).isoformat(); paid_installments += 1
            schedule_num += 1
            sid = f"SCH{schedule_num:08d}"
            schedules.append({
                "schedule_id": sid, "loan_id": lid, "installment_number": k, "due_date": due.isoformat(),
                "principal_due": money(installment * .82), "interest_due": money(installment * .18), "fees_due": "0.00",
                "total_amount_due": money(installment), "amount_paid": money(amount_paid), "outstanding_amount": money(installment - amount_paid),
                "schedule_status": sched_status, "settlement_date": settlement, "days_past_due": dpd, "created_at": iso_ts(disb),
            })
            if amount_paid > 0:
                payment_num += 1
                pay_date = due if not settlement else date.fromisoformat(settlement)
                payments.append({
                    "payment_id": f"PAY{payment_num:08d}", "loan_id": lid, "schedule_id": sid, "payment_date": pay_date.isoformat(),
                    "posting_timestamp": iso_ts(pay_date), "payment_amount": money(amount_paid), "principal_paid": money(amount_paid * .82),
                    "interest_paid": money(amount_paid * .18), "fees_paid": "0.00", "penalty_paid": "0.00",
                    "payment_channel": random.choice(["ACCOUNT_DEBIT", "MPESA", "BRANCH"]), "payment_reference": f"PMT-{uuid.uuid4().hex[:16]}",
                    "reversal_flag": False, "created_at": iso_ts(pay_date),
                })
        outstanding = max(0, principal * (1 - paid_installments / term))
        loans.append({
            "loan_id": lid, "application_id": appid, "customer_id": m["cid"], "loan_account_id": primary_account[m["cid"]], "loan_product_code": "MSME_TERM",
            "currency_code": "KES", "disbursement_date": disb.isoformat(), "maturity_date": (disb + timedelta(days=term*30)).isoformat(),
            "original_principal": money(principal), "outstanding_principal": money(outstanding), "outstanding_interest": money(outstanding*rate/12),
            "interest_rate": f"{rate*100:.4f}", "interest_rate_type": "FIXED", "term_months": term, "repayment_frequency": "MONTHLY",
            "installment_amount": money(installment), "next_payment_date": "", "days_past_due": current_dpd,
            "arrears_amount": money(installment * min(4, math.ceil(current_dpd/30))) if current_dpd else "0.00", "loan_status": status,
            "restructured_flag": is_default and random.random() < .15, "restructure_count": 1 if is_default and random.random() < .15 else 0,
            "write_off_flag": writeoff, "write_off_date": (disb + timedelta(days=random.randint(180, 330))).isoformat() if writeoff else "",
            "classification_code": classification, "collateral_value": money(principal * random.uniform(.5, 1.8)),
            "created_at": iso_ts(disb), "updated_at": iso_ts(SNAPSHOT),
        })

    # Transactions are generated after risk assignment, so risky firms show weaker and more volatile cash flow.
    account_by_customer = defaultdict(list)
    for a in accounts: account_by_customer[a["customer_id"]].append(a)
    transactions = []
    tx_start = date(2022, 7, 1)
    for i in range(1, TX_COUNT + 1):
        cid = random.choice(list(customer_meta))
        cm = customer_meta[cid]; acc = random.choice(account_by_customer[cid])
        d = between(max(tx_start, date.fromisoformat(acc["open_date"])), SNAPSHOT)
        credit = random.random() < (.48 - cm["risk"] * .06)
        base = cm["turnover"] / 12 / 18
        amount = max(100, random.lognormvariate(math.log(max(500, base)), .8 + cm["risk"]*.35))
        sign = 1 if credit else -1
        balance_after = max(0, cm["turnover"] * random.uniform(.002, .06) + sign * amount)
        transactions.append({
            "transaction_id": f"TX{i:09d}", "account_id": acc["account_id"], "customer_id": cid,
            "posting_timestamp": iso_ts(d, random.randint(7, 20)), "value_date": d.isoformat(), "transaction_code": "CR" if credit else "DR",
            "transaction_type": "CREDIT" if credit else "DEBIT", "transaction_category": random.choice(["SALES", "TRANSFER", "SUPPLIER", "PAYROLL", "CASH"]),
            "credit_debit_indicator": "C" if credit else "D", "amount": money(amount), "currency_code": "KES",
            "local_currency_amount": money(amount), "channel_code": random.choice(["MOBILE", "EFT", "RTGS", "BRANCH", "CARD"]),
            "transaction_description": "Synthetic MSME transaction", "reference_number": f"REF{i:09d}",
            "counterparty_token": f"CP-{random.randint(1,99999):05d}", "counterparty_bank_code": "", "merchant_category_code": "",
            "branch_code": acc["branch_code"], "balance_before": money(max(0, balance_after-sign*amount)), "balance_after": money(balance_after),
            "reversal_flag": False, "reversal_transaction_id": "", "cash_transaction_flag": random.random() < .18,
            "country_code": "KE", "created_at": iso_ts(d),
        })

    assessments, decisions, alerts = [], [], []
    loan_by_app = {l["application_id"]: l for l in loans}
    for i, app in enumerate(applications, 1):
        m = app_meta[app["application_id"]]
        pd = max(.01, min(.65, .02 + m["risk"]*.35 + (600-m["bureau_score"])/1600))
        score = int(max(300, min(850, 850-pd*700)))
        band = "LOW" if pd < .08 else "MEDIUM" if pd < .18 else "HIGH" if pd < .32 else "VERY_HIGH"
        assessment_id = str(uuid.uuid4())
        assessments.append({
            "assessment_id": assessment_id, "application_id": app["application_id"], "assessment_version": 1,
            "assessment_timestamp": iso_ts(m["date"]), "model_name": "SYNTHETIC_RULE_BASELINE", "model_version": "0.1",
            "credit_score": score, "probability_of_default": f"{pd:.6f}", "risk_band": band,
            "monthly_repayment_capacity": money(max(0, m["revenue"]-m["expenses"]-m["debt"])),
            "debt_service_ratio": f"{m['debt']/max(1,m['revenue']-m['expenses']):.6f}",
            "recommended_loan_limit": money(m["revenue"]*6*(1-pd)), "recommended_term_months": m["term"],
            "system_recommendation": "APPROVE" if m["approved"] else "DECLINE",
            "positive_factors": json.dumps(["Established cash flow"] if pd < .18 else []),
            "negative_factors": json.dumps(["Elevated credit risk"] if pd >= .18 else []),
            "policy_results": json.dumps({"synthetic": True}), "feature_snapshot": json.dumps({"bureau_score": m["bureau_score"]}),
            "data_completeness_score": "1.0000", "created_by": "", "created_at": iso_ts(m["date"]),
        })
        decisions.append({
            "decision_id": str(uuid.uuid4()), "application_id": app["application_id"], "assessment_id": assessment_id,
            "decision_type": "APPROVE" if m["approved"] else "DECLINE", "decision_stage": "FINAL",
            "approved_amount": loan_by_app[app["application_id"]]["original_principal"] if m["approved"] else "",
            "approved_term_months": m["term"] if m["approved"] else "", "interest_rate": loan_by_app[app["application_id"]]["interest_rate"] if m["approved"] else "",
            "decision_reason_code": "POLICY_PASS" if m["approved"] else "RISK_THRESHOLD", "decision_comments": "Synthetic historical decision",
            "override_flag": False, "override_reason": "", "decided_by": "", "decided_at": iso_ts(m["date"] + timedelta(days=1)),
        })
    for l in loans:
        if int(l["days_past_due"]) > 0:
            alerts.append({
                "alert_id": str(uuid.uuid4()), "customer_id": l["customer_id"], "loan_id": l["loan_id"], "alert_type": "DELINQUENCY",
                "severity": "CRITICAL" if int(l["days_past_due"]) >= 90 else "HIGH" if int(l["days_past_due"]) >= 60 else "MEDIUM",
                "alert_title": "Loan repayment delinquency", "alert_description": f"Loan is {l['days_past_due']} days past due",
                "trigger_value": l["days_past_due"], "threshold_value": 30, "alert_status": "OPEN", "assigned_to": "",
                "detected_at": iso_ts(SNAPSHOT), "acknowledged_at": "", "resolved_at": "", "resolution_notes": "", "created_at": iso_ts(SNAPSHOT),
            })

    datasets = [
        ("customers.csv", customers), ("accounts.csv", accounts), ("account_transactions.csv", transactions),
        ("loan_applications.csv", applications), ("credit_bureau_reports.csv", bureaus), ("credit_assessments.csv", assessments),
        ("credit_decisions.csv", decisions), ("loans.csv", loans), ("repayment_schedule.csv", schedules),
        ("loan_payments.csv", payments), ("risk_alerts.csv", alerts),
    ]
    for filename, rows in datasets:
        write_csv(filename, list(rows[0].keys()), rows)
    print(f"\nHistorical approved loans: {len(approved_historical):,}")
    print(f"Historical defaults:      {len(default_apps):,} ({len(default_apps)/len(approved_historical):.2%})")
    print(f"Output directory:         {OUT}")
    print("users.csv and audit_logs.csv are intentionally preserved if already present.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate model-ready MSME credit data")
    parser.parse_args()
    main()