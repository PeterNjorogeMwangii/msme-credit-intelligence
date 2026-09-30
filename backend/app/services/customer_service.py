import math
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.schemas.customer import (
    Customer360Response,
    CustomerFinancialSummary,
    CustomerListItem,
    CustomerListResponse,
    CustomerProfile,
    CustomerRiskSummary,
)


class CustomerService:
    def __init__(self, database: Session) -> None:
        self.repository = CustomerRepository(database)

    def list_customers(
        self,
        page: int,
        page_size: int,
        search: Optional[str] = None,
        customer_status: Optional[str] = None,
        risk_band: Optional[str] = None,
    ) -> CustomerListResponse:
        total_records = self.repository.count_customers(
            search=search,
            status=customer_status,
            risk_band=risk_band,
        )
        records = self.repository.list_customers(
            offset=(page - 1) * page_size,
            limit=page_size,
            search=search,
            status=customer_status,
            risk_band=risk_band,
        )
        total_pages = math.ceil(total_records / page_size) if total_records else 0
        return CustomerListResponse(
            page=page,
            page_size=page_size,
            total_records=total_records,
            total_pages=total_pages,
            records=[CustomerListItem.model_validate(record) for record in records],
        )

    def get_customer_360(self, customer_id: str) -> Customer360Response:
        customer = self.repository.get_customer(customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer {customer_id} was not found.",
            )

        financial = self.repository.get_financial_summary(customer_id)
        risk = self.repository.get_risk_summary(customer_id)

        return Customer360Response(
            customer=CustomerProfile.model_validate(customer),
            financial_summary=CustomerFinancialSummary(**financial),
            risk_summary=CustomerRiskSummary(**risk),
            accounts=self.repository.get_accounts(customer_id),
            recent_transactions=self.repository.get_recent_transactions(customer_id),
            loan_applications=self.repository.get_loan_applications(customer_id),
            loans=self.repository.get_loans(customer_id),
            risk_alerts=self.repository.get_risk_alerts(customer_id),
            activity_timeline=self.repository.get_activity_timeline(customer_id),
        )
