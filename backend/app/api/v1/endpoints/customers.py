from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.schemas.customer import (
    Customer360Response,
    CustomerListResponse,
)
from backend.app.services.customer_service import (
    CustomerService,
)


router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


@router.get(
    "",
    response_model=CustomerListResponse,
    summary="List and search MSME customers",
)
def list_customers(
    page: Annotated[
        int,
        Query(ge=1),
    ] = 1,
    page_size: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 20,
    search: Optional[str] = None,
    customer_status: Annotated[
        Optional[str],
        Query(
            pattern=(
                "^(ACTIVE|INACTIVE|CLOSED)$"
            )
        ),
    ] = None,
    risk_band: Annotated[
        Optional[str],
        Query(
            pattern=(
                "^(VERY_LOW|LOW|MEDIUM|"
                "HIGH|VERY_HIGH)$"
            )
        ),
    ] = None,
    database: Session = Depends(get_db),
) -> CustomerListResponse:
    service = CustomerService(database)

    return service.list_customers(
        page=page,
        page_size=page_size,
        search=search,
        customer_status=customer_status,
        risk_band=risk_band,
    )


@router.get(
    "/{customer_id}",
    response_model=Customer360Response,
    summary="Get an MSME Customer 360 summary",
)
def get_customer(
    customer_id: str,
    database: Session = Depends(get_db),
) -> Customer360Response:
    service = CustomerService(database)

    return service.get_customer_360(
        customer_id
    )