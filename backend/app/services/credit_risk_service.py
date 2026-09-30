from __future__ import annotations

import json
import math
from datetime import date, datetime, timezone
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import joblib
import numpy as np
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session


@lru_cache(maxsize=1)
def _load_model_artifacts(
    model_path: str,
    metadata_path: str,
) -> tuple[Any, dict[str, Any]]:
    pipeline = joblib.load(model_path)
    metadata = json.loads(Path(metadata_path).read_text(encoding="utf-8"))
    return pipeline, metadata


class ApplicationNotFoundError(Exception):
    pass


class AssessmentNotFoundError(Exception):
    pass


class CreditRiskService:
    MODEL_NAME = "random_forest"
    MODEL_VERSION = "model_comparison_v1"
    DEFAULT_THRESHOLD = 0.363984
    IDENTIFIER_COLUMNS = {"application_id", "customer_id", "application_date"}

    def __init__(self, database: Session):
        self.database = database

        backend_root = Path(__file__).resolve().parents[2]
        self.artifact_dir = (
            backend_root / "ml" / "artifacts" / self.MODEL_VERSION
        )
        self.model_path = (
            self.artifact_dir / "champion_credit_risk_pipeline.joblib"
        )
        self.metadata_path = self.artifact_dir / "champion_metadata.json"

        if not self.model_path.exists():
            raise RuntimeError(f"Champion model not found: {self.model_path}")
        if not self.metadata_path.exists():
            raise RuntimeError(f"Model metadata not found: {self.metadata_path}")

        self.pipeline, self.metadata = _load_model_artifacts(
            str(self.model_path),
            str(self.metadata_path),
        )
        self.feature_columns = self._metadata_list(
            "feature_columns", "features", "model_features"
        )
        self.categorical_columns = self._metadata_list(
            "categorical_features", "categorical_columns", required=False
        )
        self.threshold = float(
            self.metadata.get(
                "threshold",
                self.metadata.get(
                    "decision_threshold",
                    self.metadata.get("selected_threshold", self.DEFAULT_THRESHOLD),
                ),
            )
        )

    def _metadata_list(
        self,
        *keys: str,
        required: bool = True,
    ) -> list[str]:
        for key in keys:
            value = self.metadata.get(key)
            if isinstance(value, list) and value:
                return [str(item) for item in value]
        if required:
            raise RuntimeError(
                f"Model metadata does not contain any of: {', '.join(keys)}"
            )
        return []

    @staticmethod
    def _json_value(value: Any) -> Any:
        if value is None or value is pd.NA:
            return None
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (np.integer,)):
            return int(value)
        if isinstance(value, (np.floating,)):
            return None if np.isnan(value) else float(value)
        if isinstance(value, (np.bool_,)):
            return bool(value)
        try:
            if pd.isna(value):
                return None
        except (TypeError, ValueError):
            pass
        return value

    @staticmethod
    def _number(features: dict[str, Any], name: str) -> float:
        value = features.get(name)
        if value is None:
            return 0.0
        return float(value)

    def _get_features(self, application_id: str) -> dict[str, Any]:
        row = self.database.execute(
            text(
                """
                SELECT *
                FROM credit.ml_scoring_features_v1
                WHERE application_id = :application_id
                """
            ),
            {"application_id": application_id},
        ).mappings().one_or_none()

        if row is None:
            raise ApplicationNotFoundError(application_id)
        return dict(row)

    def _predict(self, features: dict[str, Any]) -> float:
        missing = [
            column for column in self.feature_columns if column not in features
        ]
        if missing:
            raise RuntimeError(f"Scoring view is missing model features: {missing}")

        frame = pd.DataFrame(
            [{column: features[column] for column in self.feature_columns}]
        )
        for column in self.categorical_columns:
            if column in frame.columns:
                frame[column] = frame[column].astype("string")

        probability = float(self.pipeline.predict_proba(frame)[:, 1][0])
        if not 0 <= probability <= 1:
            raise RuntimeError("Model returned an invalid probability")
        return probability

    def _risk_band(self, probability: float) -> tuple[str, str]:
        if probability < 0.10:
            return "VERY_LOW", "RECOMMEND_APPROVAL"
        if probability < 0.20:
            return "LOW", "RECOMMEND_APPROVAL"
        if probability < self.threshold:
            return "MEDIUM", "REFER_FOR_APPROVAL"
        if probability < 0.60:
            return "HIGH", "REFER_FOR_ENHANCED_REVIEW"
        return "VERY_HIGH", "RECOMMEND_DECLINE"

    def _capacity(self, features: dict[str, Any]) -> dict[str, Any]:
        revenue = self._number(features, "declared_monthly_revenue")
        expenses = self._number(features, "declared_monthly_expenses")
        existing_debt = self._number(features, "existing_monthly_debt")
        requested_amount = self._number(features, "requested_amount")
        turnover = self._number(features, "annual_turnover_declared")
        requested_term = max(
            int(self._number(features, "requested_term_months")), 1
        )

        monthly_surplus = max(revenue - expenses - existing_debt, 0.0)
        repayment_capacity = monthly_surplus * 0.40
        debt_service_ratio = existing_debt / revenue if revenue > 0 else None

        capacity_limit = repayment_capacity * requested_term * 0.70
        turnover_limit = turnover * 0.30 if turnover > 0 else requested_amount
        recommended_limit = max(
            0.0,
            min(requested_amount, capacity_limit, turnover_limit),
        )
        return {
            "monthly_repayment_capacity": round(repayment_capacity, 2),
            "debt_service_ratio": (
                round(debt_service_ratio, 6)
                if debt_service_ratio is not None
                else None
            ),
            "recommended_loan_limit": round(recommended_limit, 2),
            "recommended_term_months": requested_term,
        }

    def _factors(
        self,
        features: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        positive: list[dict[str, Any]] = []
        negative: list[dict[str, Any]] = []

        bureau = self._number(features, "bureau_score")
        dpd = self._number(features, "previous_max_dpd_12m")
        delinquent = self._number(features, "delinquent_facilities")
        margin = self._number(features, "declared_operating_margin")
        cash_flow = self._number(features, "net_cash_flow_180d")
        collateral = self._number(features, "collateral_coverage_ratio")
        debit_ratio = self._number(features, "debit_to_credit_ratio_180d")

        if bureau >= 700:
            positive.append({"code": "STRONG_BUREAU_SCORE", "value": bureau})
        elif bureau < 600:
            negative.append({"code": "LOW_BUREAU_SCORE", "value": bureau})
        if dpd == 0:
            positive.append({"code": "NO_RECENT_ARREARS", "value": dpd})
        elif dpd > 0:
            negative.append({"code": "RECENT_DAYS_PAST_DUE", "value": dpd})
        if delinquent > 0:
            negative.append(
                {"code": "DELINQUENT_FACILITIES", "value": delinquent}
            )
        if margin >= 0.20:
            positive.append({"code": "HEALTHY_OPERATING_MARGIN", "value": margin})
        elif margin < 0.10:
            negative.append({"code": "LOW_OPERATING_MARGIN", "value": margin})
        if cash_flow > 0:
            positive.append({"code": "POSITIVE_NET_CASH_FLOW", "value": cash_flow})
        elif cash_flow < 0:
            negative.append({"code": "NEGATIVE_NET_CASH_FLOW", "value": cash_flow})
        if collateral >= 1:
            positive.append({"code": "FULL_COLLATERAL_COVERAGE", "value": collateral})
        if debit_ratio > 1.20:
            negative.append({"code": "HIGH_DEBIT_TO_CREDIT_RATIO", "value": debit_ratio})

        return positive[:5], negative[:5]

    def _policy(
        self,
        features: dict[str, Any],
        recommendation: str,
        completeness: float,
    ) -> tuple[str, dict[str, Any]]:
        rules: list[dict[str, Any]] = []

        adverse = bool(features.get("adverse_listing_flag", False))
        write_offs = int(self._number(features, "written_off_facilities"))
        legal_cases = int(self._number(features, "legal_cases"))

        rules.append({"rule": "ADVERSE_LISTING", "passed": not adverse})
        rules.append({"rule": "NO_WRITE_OFF", "passed": write_offs == 0})
        rules.append({"rule": "NO_LEGAL_CASE", "passed": legal_cases == 0})
        rules.append(
            {"rule": "MINIMUM_DATA_COMPLETENESS", "passed": completeness >= 70}
        )

        if adverse or write_offs > 0:
            recommendation = "RECOMMEND_DECLINE"
        elif legal_cases > 0:
            recommendation = "REFER_FOR_ENHANCED_REVIEW"
        elif completeness < 70:
            recommendation = "REQUEST_MORE_INFORMATION"

        return recommendation, {
            "all_rules_passed": all(item["passed"] for item in rules),
            "rules": rules,
            "model_decision_threshold": self.threshold,
        }

    def score_application(
        self,
        application_id: str,
        created_by: UUID | None = None,
    ) -> dict[str, Any]:
        features = self._get_features(application_id)
        model_inputs = [features.get(column) for column in self.feature_columns]
        present = sum(value is not None for value in model_inputs)
        completeness = round(100 * present / len(self.feature_columns), 2)

        probability = self._predict(features)
        risk_band, recommendation = self._risk_band(probability)
        capacity = self._capacity(features)
        positive, negative = self._factors(features)
        recommendation, policy_results = self._policy(
            features, recommendation, completeness
        )
        credit_score = max(300, min(850, round(850 - probability * 550)))

        snapshot = {
            key: self._json_value(features.get(key))
            for key in self.feature_columns
        }
        assessment_id = uuid4()
        now = datetime.now(timezone.utc)

        # Serialize scoring of the same application so version numbers stay unique.
        self.database.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:application_id))"),
            {"application_id": application_id},
        )
        version = self.database.execute(
            text(
                """
                SELECT COALESCE(MAX(assessment_version), 0) + 1
                FROM credit.credit_assessments
                WHERE application_id = :application_id
                """
            ),
            {"application_id": application_id},
        ).scalar_one()

        payload = {
            "assessment_id": assessment_id,
            "application_id": application_id,
            "assessment_version": int(version),
            "assessment_timestamp": now,
            "model_name": self.MODEL_NAME,
            "model_version": self.MODEL_VERSION,
            "credit_score": credit_score,
            "probability_of_default": round(probability, 8),
            "risk_band": risk_band,
            **capacity,
            "system_recommendation": recommendation,
            "positive_factors": positive,
            "negative_factors": negative,
            "policy_results": policy_results,
            "feature_snapshot": snapshot,
            "data_completeness_score": completeness,
            "created_by": created_by,
            "created_at": now,
        }

        insert_parameters = payload | {
            "positive_factors_json": json.dumps(positive),
            "negative_factors_json": json.dumps(negative),
            "policy_results_json": json.dumps(policy_results),
            "feature_snapshot_json": json.dumps(snapshot),
        }
        self.database.execute(
            text(
                """
                INSERT INTO credit.credit_assessments (
                    assessment_id, application_id, assessment_version,
                    assessment_timestamp, model_name, model_version,
                    credit_score, probability_of_default, risk_band,
                    monthly_repayment_capacity, debt_service_ratio,
                    recommended_loan_limit, recommended_term_months,
                    system_recommendation, positive_factors, negative_factors,
                    policy_results, feature_snapshot, data_completeness_score,
                    created_by, created_at
                ) VALUES (
                    :assessment_id, :application_id, :assessment_version,
                    :assessment_timestamp, :model_name, :model_version,
                    :credit_score, :probability_of_default, :risk_band,
                    :monthly_repayment_capacity, :debt_service_ratio,
                    :recommended_loan_limit, :recommended_term_months,
                    :system_recommendation,
                    CAST(:positive_factors_json AS jsonb),
                    CAST(:negative_factors_json AS jsonb),
                    CAST(:policy_results_json AS jsonb),
                    CAST(:feature_snapshot_json AS jsonb),
                    :data_completeness_score, :created_by, :created_at
                )
                """
            ),
            insert_parameters,
        )
        self.database.commit()
        return payload

    def latest_assessment(self, application_id: str) -> dict[str, Any]:
        row = self.database.execute(
            text(
                """
                SELECT assessment_id, application_id, assessment_version,
                       assessment_timestamp, model_name, model_version,
                       credit_score, probability_of_default, risk_band,
                       monthly_repayment_capacity, debt_service_ratio,
                       recommended_loan_limit, recommended_term_months,
                       system_recommendation, positive_factors,
                       negative_factors, policy_results,
                       data_completeness_score, created_at
                FROM credit.credit_assessments
                WHERE application_id = :application_id
                ORDER BY assessment_version DESC
                LIMIT 1
                """
            ),
            {"application_id": application_id},
        ).mappings().one_or_none()
        if row is None:
            raise AssessmentNotFoundError(application_id)
        return dict(row)

    @staticmethod
    def _latest_assessments_cte() -> str:
        return """
            WITH latest_assessments AS (
                SELECT DISTINCT ON (ca.application_id)
                       ca.assessment_id,
                       ca.application_id,
                       ca.assessment_version,
                       ca.assessment_timestamp,
                       ca.credit_score,
                       ca.probability_of_default,
                       ca.risk_band,
                       ca.system_recommendation,
                       ca.recommended_loan_limit
                FROM credit.credit_assessments ca
                ORDER BY ca.application_id,
                         ca.assessment_version DESC,
                         ca.assessment_timestamp DESC
            )
        """

    def portfolio_summary(self) -> dict[str, Any]:
        cte = self._latest_assessments_cte()
        totals = self.database.execute(
            text(
                cte
                + """
                SELECT COUNT(*)::integer AS total_assessed_applications,
                       COALESCE(AVG(credit_score), 0)::numeric AS average_credit_score,
                       COALESCE(AVG(probability_of_default), 0)::numeric
                           AS average_probability_of_default,
                       COUNT(*) FILTER (
                           WHERE risk_band IN ('HIGH', 'VERY_HIGH')
                       )::integer AS high_risk_applications,
                       COUNT(*) FILTER (
                           WHERE system_recommendation IN (
                               'REFER_FOR_APPROVAL',
                               'REFER_FOR_ENHANCED_REVIEW',
                               'REQUEST_MORE_INFORMATION'
                           )
                       )::integer AS review_queue_count
                FROM latest_assessments
                """
            )
        ).mappings().one()

        bands = self.database.execute(
            text(
                cte
                + """
                SELECT risk_band,
                       COUNT(*)::integer AS application_count,
                       ROUND(
                           100.0 * COUNT(*) / NULLIF(SUM(COUNT(*)) OVER (), 0),
                           2
                       ) AS percentage,
                       COALESCE(AVG(probability_of_default), 0)::numeric
                           AS average_probability_of_default
                FROM latest_assessments
                GROUP BY risk_band
                ORDER BY CASE risk_band
                    WHEN 'VERY_LOW' THEN 1
                    WHEN 'LOW' THEN 2
                    WHEN 'MEDIUM' THEN 3
                    WHEN 'HIGH' THEN 4
                    WHEN 'VERY_HIGH' THEN 5
                    ELSE 6
                END
                """
            )
        ).mappings().all()

        return {
            "total_assessed_applications": totals["total_assessed_applications"],
            "average_credit_score": round(float(totals["average_credit_score"]), 2),
            "average_probability_of_default": round(
                float(totals["average_probability_of_default"]), 6
            ),
            "high_risk_applications": totals["high_risk_applications"],
            "review_queue_count": totals["review_queue_count"],
            "risk_bands": [
                {
                    "risk_band": row["risk_band"],
                    "application_count": row["application_count"],
                    "percentage": float(row["percentage"]),
                    "average_probability_of_default": round(
                        float(row["average_probability_of_default"]), 6
                    ),
                }
                for row in bands
            ],
        }

    def list_assessments(
        self,
        page: int,
        page_size: int,
        search: str | None = None,
        risk_band: str | None = None,
        recommendation: str | None = None,
    ) -> dict[str, Any]:
        cte = self._latest_assessments_cte()
        conditions = ["1 = 1"]
        parameters: dict[str, Any] = {}

        if search:
            conditions.append(
                "(la.application_id ILIKE :search "
                "OR c.customer_id ILIKE :search "
                "OR c.legal_name ILIKE :search "
                "OR c.trading_name ILIKE :search)"
            )
            parameters["search"] = f"%{search.strip()}%"
        if risk_band:
            conditions.append("la.risk_band = :risk_band")
            parameters["risk_band"] = risk_band
        if recommendation:
            conditions.append("la.system_recommendation = :recommendation")
            parameters["recommendation"] = recommendation

        where_clause = " AND ".join(conditions)
        from_clause = """
            FROM latest_assessments la
            JOIN credit.loan_applications app
              ON app.application_id = la.application_id
            JOIN banking.customers c
              ON c.customer_id = app.customer_id
        """

        total_items = self.database.execute(
            text(cte + " SELECT COUNT(*) " + from_clause + " WHERE " + where_clause),
            parameters,
        ).scalar_one()

        parameters |= {
            "limit": page_size,
            "offset": (page - 1) * page_size,
        }
        rows = self.database.execute(
            text(
                cte
                + """
                SELECT la.assessment_id,
                       la.application_id,
                       app.customer_id,
                       COALESCE(c.trading_name, c.legal_name) AS business_name,
                       app.requested_amount,
                       app.application_status,
                       la.assessment_version,
                       la.assessment_timestamp,
                       la.credit_score,
                       la.probability_of_default,
                       la.risk_band,
                       la.system_recommendation,
                       la.recommended_loan_limit
                """
                + from_clause
                + " WHERE "
                + where_clause
                + """
                ORDER BY la.assessment_timestamp DESC,
                         la.application_id
                LIMIT :limit OFFSET :offset
                """
            ),
            parameters,
        ).mappings().all()

        return {
            "items": [dict(row) for row in rows],
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": math.ceil(total_items / page_size) if total_items else 0,
        }

    def review_queue(
        self,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        # Reuse the same pagination contract and restrict to analyst-action outcomes.
        cte = self._latest_assessments_cte()
        condition = """
            la.system_recommendation IN (
                'REFER_FOR_APPROVAL',
                'REFER_FOR_ENHANCED_REVIEW',
                'REQUEST_MORE_INFORMATION'
            )
        """
        from_clause = """
            FROM latest_assessments la
            JOIN credit.loan_applications app
              ON app.application_id = la.application_id
            JOIN banking.customers c
              ON c.customer_id = app.customer_id
        """
        total_items = self.database.execute(
            text(cte + " SELECT COUNT(*) " + from_clause + " WHERE " + condition)
        ).scalar_one()
        rows = self.database.execute(
            text(
                cte
                + """
                SELECT la.assessment_id,
                       la.application_id,
                       app.customer_id,
                       COALESCE(c.trading_name, c.legal_name) AS business_name,
                       app.requested_amount,
                       app.application_status,
                       la.assessment_version,
                       la.assessment_timestamp,
                       la.credit_score,
                       la.probability_of_default,
                       la.risk_band,
                       la.system_recommendation,
                       la.recommended_loan_limit
                """
                + from_clause
                + " WHERE "
                + condition
                + """
                ORDER BY CASE la.system_recommendation
                    WHEN 'REFER_FOR_ENHANCED_REVIEW' THEN 1
                    WHEN 'REQUEST_MORE_INFORMATION' THEN 2
                    ELSE 3
                END,
                la.probability_of_default DESC,
                la.assessment_timestamp DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            {"limit": page_size, "offset": (page - 1) * page_size},
        ).mappings().all()
        return {
            "items": [dict(row) for row in rows],
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": math.ceil(total_items / page_size) if total_items else 0,
        }

    def probability_distribution(self) -> dict[str, Any]:
        cte = self._latest_assessments_cte()
        rows = self.database.execute(
            text(
                cte
                + """
                , bucket_definitions AS (
                    SELECT * FROM (VALUES
                        (1, '0.00-0.10', 0.00::numeric, 0.10::numeric),
                        (2, '0.10-0.20', 0.10::numeric, 0.20::numeric),
                        (3, '0.20-0.36', 0.20::numeric, 0.363984::numeric),
                        (4, '0.36-0.60', 0.363984::numeric, 0.60::numeric),
                        (5, '0.60-1.00', 0.60::numeric, 1.000001::numeric)
                    ) AS b(sort_order, bucket, lower_bound, upper_bound)
                ), totals AS (
                    SELECT COUNT(*)::integer AS total
                    FROM latest_assessments
                )
                SELECT b.bucket,
                       b.lower_bound,
                       CASE WHEN b.upper_bound > 1 THEN 1 ELSE b.upper_bound END
                           AS upper_bound,
                       COUNT(la.application_id)::integer AS application_count,
                       ROUND(
                           100.0 * COUNT(la.application_id) / NULLIF(t.total, 0),
                           2
                       ) AS percentage
                FROM bucket_definitions b
                CROSS JOIN totals t
                LEFT JOIN latest_assessments la
                  ON la.probability_of_default >= b.lower_bound
                 AND la.probability_of_default < b.upper_bound
                GROUP BY b.sort_order, b.bucket, b.lower_bound, b.upper_bound, t.total
                ORDER BY b.sort_order
                """
            )
        ).mappings().all()
        total = sum(row["application_count"] for row in rows)
        return {
            "total_applications": total,
            "buckets": [
                {
                    "bucket": row["bucket"],
                    "lower_bound": float(row["lower_bound"]),
                    "upper_bound": float(row["upper_bound"]),
                    "application_count": row["application_count"],
                    "percentage": float(row["percentage"] or 0),
                }
                for row in rows
            ],
        }

    def high_risk_customers(
        self,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        cte = self._latest_assessments_cte()
        from_clause = """
            FROM latest_assessments la
            JOIN credit.loan_applications app
              ON app.application_id = la.application_id
            JOIN banking.customers c
              ON c.customer_id = app.customer_id
        """
        condition = "la.risk_band IN ('HIGH', 'VERY_HIGH')"
        total_items = self.database.execute(
            text(cte + " SELECT COUNT(*) " + from_clause + " WHERE " + condition)
        ).scalar_one()
        rows = self.database.execute(
            text(
                cte
                + """
                SELECT la.assessment_id,
                       la.application_id,
                       app.customer_id,
                       COALESCE(c.trading_name, c.legal_name) AS business_name,
                       app.requested_amount,
                       app.application_status,
                       la.assessment_version,
                       la.assessment_timestamp,
                       la.credit_score,
                       la.probability_of_default,
                       la.risk_band,
                       la.system_recommendation,
                       la.recommended_loan_limit
                """
                + from_clause
                + " WHERE "
                + condition
                + """
                ORDER BY la.probability_of_default DESC,
                         la.assessment_timestamp DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            {"limit": page_size, "offset": (page - 1) * page_size},
        ).mappings().all()
        return {
            "items": [dict(row) for row in rows],
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": math.ceil(total_items / page_size) if total_items else 0,
        }

    def recent_activity(self, limit: int) -> list[dict[str, Any]]:
        rows = self.database.execute(
            text(
                """
                SELECT ca.assessment_id,
                       ca.application_id,
                       app.customer_id,
                       COALESCE(c.trading_name, c.legal_name) AS business_name,
                       ca.assessment_timestamp,
                       ca.credit_score,
                       ca.probability_of_default,
                       ca.risk_band,
                       ca.system_recommendation
                FROM credit.credit_assessments ca
                JOIN credit.loan_applications app
                  ON app.application_id = ca.application_id
                JOIN banking.customers c
                  ON c.customer_id = app.customer_id
                ORDER BY ca.assessment_timestamp DESC,
                         ca.created_at DESC
                LIMIT :limit
                """
            ),
            {"limit": limit},
        ).mappings().all()
        return [dict(row) for row in rows]

    def model_info(self) -> dict[str, Any]:
        return {
            "model_name": self.MODEL_NAME,
            "model_version": self.MODEL_VERSION,
            "feature_count": len(self.feature_columns),
            "decision_threshold": self.threshold,
            "risk_bands": {
                "VERY_LOW": "0.0000-0.0999",
                "LOW": "0.1000-0.1999",
                "MEDIUM": f"0.2000-{self.threshold - 0.000001:.6f}",
                "HIGH": f"{self.threshold:.6f}-0.5999",
                "VERY_HIGH": "0.6000-1.0000",
            },
            "artifact_path": str(self.model_path),
        }
