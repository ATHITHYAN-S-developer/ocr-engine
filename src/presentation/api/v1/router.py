from fastapi import APIRouter
from src.presentation.api.v1.endpoints import auth, projects, documents, jobs, results, health

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects & API Keys"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["OCR Jobs"])
api_router.include_router(results.router, prefix="/results", tags=["OCR Results"])
api_router.include_router(health.router, prefix="/health", tags=["System Health"])
