from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from fastapi.responses import StreamingResponse
import io
from datetime import datetime
import uuid
from src.presentation.schemas import OCRResultResponse
from src.presentation.api.dependencies import (
    get_authenticated_project_id, get_db
)
from src.infrastructure.database.repositories import (
    SQLOCRResultRepository, SQLExportRepository, SQLOCRJobRepository
)
from src.infrastructure.storage.service import get_storage_service
from src.infrastructure.exporters.service import generate_export_format
from src.domain.entities.export import Export

router = APIRouter()

@router.get("/{job_id}", response_model=OCRResultResponse)
def get_ocr_result(
    job_id: str,
    project_id: str = Depends(get_authenticated_project_id),
    db = Depends(get_db)
):
    """Retrieves full structured OCR JSON output for a finished job."""
    job_repo = SQLOCRJobRepository(db)
    job = job_repo.get_by_id(job_id)
    if not job or job.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
        
    if job.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"OCR job results are not ready. Job status: {job.status}"
        )

    res_repo = SQLOCRResultRepository(db)
    result = res_repo.get_by_job_id(job_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OCR result record not found.")
    return result

@router.get("/download/{job_id}/export")
def download_export(
    job_id: str,
    format_name: str = Query(..., alias="format", description="Export format: JSON, TXT, MD, CSV, XML, DOCX, PDF"),
    project_id: str = Depends(get_authenticated_project_id),
    db = Depends(get_db)
):
    """
    Downloads an OCR result in the requested export format.
    If the export file was not pre-generated, it generates it on the fly, 
    persists it to storage, and streams it back.
    """
    fmt = format_name.upper().strip()
    allowed_formats = ["JSON", "TXT", "MD", "CSV", "XML", "DOCX", "PDF"]
    if fmt not in allowed_formats:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Supported formats: {allowed_formats}")

    job_repo = SQLOCRJobRepository(db)
    job = job_repo.get_by_id(job_id)
    if not job or job.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OCR Job not found.")

    if job.status != "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Job is not completed yet. Status: {job.status}")

    res_repo = SQLOCRResultRepository(db)
    result = res_repo.get_by_job_id(job_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OCR Result data missing.")

    export_repo = SQLExportRepository(db)
    storage = get_storage_service()

    # Try to fetch existing pre-generated export file
    export_record = export_repo.get_by_job_and_format(job_id, fmt)
    
    # MIME Types mapping
    mime_types = {
        "JSON": "application/json",
        "TXT": "text/plain",
        "MD": "text/markdown",
        "CSV": "text/csv",
        "XML": "application/xml",
        "DOCX": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "PDF": "application/pdf"
    }
    
    file_bytes = None
    filename = f"export_{job_id}.{fmt.lower()}"

    if export_record:
        try:
            file_bytes = storage.download_file(export_record.file_path)
        except Exception:
            # Fallback to generating on the fly if stored file disappeared
            pass

    if file_bytes is None:
        # Generate on the fly
        try:
            file_bytes = generate_export_format(result.structured_json, fmt)
            # Upload generated export
            dest_path = f"exports/{job_id}/dynamic_export_{fmt.lower()}_{uuid.uuid4().hex[:8]}.{fmt.lower()}"
            uploaded_path = storage.upload_file(file_bytes, dest_path)
            
            # Save export record to DB
            new_export = Export(
                id=str(uuid.uuid4()),
                job_id=job_id,
                format=fmt,
                file_path=uploaded_path,
                created_at=datetime.utcnow()
            )
            export_repo.add(new_export)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Export generation failed: {str(e)}")

    # Return standard HTTP Response
    return Response(
        content=file_bytes,
        media_type=mime_types[fmt],
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
