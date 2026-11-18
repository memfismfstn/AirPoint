from fastapi import APIRouter

from src.presentation.api.routers import customers, drones, licenses, parts

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(drones.router)
api_router.include_router(parts.router)
api_router.include_router(customers.router)
api_router.include_router(licenses.router)
