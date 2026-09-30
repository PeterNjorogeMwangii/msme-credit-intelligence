from typing import Optional, List
from sqlalchemy.orm import Session
from backend.app.models.customer import Customer


class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def count_customers(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        risk_band: Optional[str] = None,
    ) -> int:
        query = self.db.query(Customer)
        
        if search:
            query = query.filter(
                Customer.business_name.ilike(f"%{search}%")
            )
        if status:
            query = query.filter(Customer.status == status)
        if risk_band:
            query = query.filter(Customer.risk_band == risk_band)
        
        return query.count()

    def list_customers(
        self,
        offset: int,
        limit: int,
        search: Optional[str] = None,
        status: Optional[str] = None,
        risk_band: Optional[str] = None,
    ) -> List[Customer]:
        query = self.db.query(Customer)
        
        if search:
            query = query.filter(
                Customer.business_name.ilike(f"%{search}%")
            )
        if status:
            query = query.filter(Customer.status == status)
        if risk_band:
            query = query.filter(Customer.risk_band == risk_band)
        
        return query.offset(offset).limit(limit).all()

    def get_customer(self, customer_id: str) -> Optional[Customer]:
        return (
            self.db.query(Customer)
            .filter(Customer.customer_id == customer_id)
            .first()
        )

    def get_financial_summary(self, customer_id: str) -> dict:
        # Implement based on your schema
        pass

    def get_risk_summary(self, customer_id: str) -> dict:
        # Implement based on your schema
        pass

    def create(self, customer: Customer) -> Customer:
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer