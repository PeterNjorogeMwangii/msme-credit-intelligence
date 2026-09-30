from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String, primary_key=True)
    customer_number = Column(String, nullable=True)
    customer_type = Column(String, nullable=True)
    legal_name = Column(String, nullable=True)
    trading_name = Column(String, nullable=True)
    registration_number = Column(String, nullable=True)
    tax_identifier = Column(String, nullable=True)
    business_type = Column(String, nullable=True)
    industry_code = Column(String, nullable=True)
    industry_description = Column(String, nullable=True)
    incorporation_date = Column(DateTime, nullable=True)
    relationship_start_date = Column(DateTime, nullable=True)
    employee_count = Column(Integer, nullable=True)
    annual_turnover_declared = Column(Integer, nullable=True)
    turnover_currency = Column(String, nullable=True)
    county_code = Column(String, nullable=True)
    branch_code = Column(String, nullable=True)
    relationship_manager_id = Column(String, nullable=True)
    kyc_status = Column(String, nullable=True)
    kyc_review_date = Column(DateTime, nullable=True)
    aml_risk_classification = Column(String, nullable=True)
    pep_flag = Column(String, nullable=True)
    sanctions_match_flag = Column(String, nullable=True)
    record_status = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)