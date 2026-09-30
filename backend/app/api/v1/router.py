from fastapi import APIRouter, Depends

from backend.app.api.dependencies.auth import get_current_user
from backend.app.api.v1.endpoints.administration import router as administration_router
from backend.app.api.v1.endpoints.alerts import router as alerts_router
from backend.app.api.v1.endpoints.auth import router as auth_router
from backend.app.api.v1.endpoints.credit_risk import router as credit_risk_router
from backend.app.api.v1.endpoints.customers import router as customers_router
from backend.app.api.v1.endpoints.health import router as health_router
from backend.app.api.v1.endpoints.transactions import router as transactions_router


api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)

protected_router = APIRouter(dependencies=[Depends(get_current_user)])
protected_router.include_router(customers_router)
protected_router.include_router(credit_risk_router)
protected_router.include_router(alerts_router)
protected_router.include_router(transactions_router)
protected_router.include_router(administration_router)
api_router.include_router(protected_router)
