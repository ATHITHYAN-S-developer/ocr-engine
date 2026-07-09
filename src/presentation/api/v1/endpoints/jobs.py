from fastapi import APIRouter, Depends, HTTPException, status
from src.presentation.schemas import JobCreate, JobResponse
from src.presentation.api.dependencies import (
    get_job_use_cases, get_authenticated_project_id, get_db
)
from src.infrastructure.database.repositories import SQLOCRJobRepository

router = APIRouter()

@router.post("", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
def submit_ocr_job(
    job_in: JobCreate,
    project_id: str = Depends(get_authenticated_project_id),
    start_job_uc = Depends(get_job_use_cases)
):
    """Submits a document to the OCR pipeline. Returns job metadata and starts Celery processing."""
    try:
        job = start_job_uc.execute(project_id, job_in.document_id, job_in.engine_config)
        return job
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{job_id}", response_model=JobResponse)
def get_job_status(
    job_id: str,
    project_id: str = Depends(get_authenticated_project_id),
    db = Depends(get_db)
):
    """Checks the processing state, current stage, and progress percentage of an OCR job."""
    job_repo = SQLOCRJobRepository(db)
    job = job_repo.get_by_id(job_id)
    if not job or job.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    return job
