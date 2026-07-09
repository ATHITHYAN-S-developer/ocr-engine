import os
import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from src.presentation.schemas import DocumentResponse, ChunkUploadResponse
from src.presentation.api.dependencies import (
    get_document_use_cases, get_authenticated_project_id, get_db
)
from src.infrastructure.database.repositories import SQLDocumentRepository, SQLUploadRepository
from src.infrastructure.storage.service import get_storage_service
from src.domain.entities.upload import Upload
from src.config import settings

router = APIRouter()

@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    project_id: str = Depends(get_authenticated_project_id),
    upload_uc = Depends(get_document_use_cases)
):
    """Single file upload endpoint."""
    content = await file.read()
    try:
        document = upload_uc.execute(project_id, file.filename, file.filename.split(".")[-1], content)
        return document
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/batch", response_model=List[DocumentResponse], status_code=status.HTTP_201_CREATED)
async def upload_batch_documents(
    files: List[UploadFile] = File(...),
    project_id: str = Depends(get_authenticated_project_id),
    upload_uc = Depends(get_document_use_cases)
):
    """Batch upload endpoint."""
    responses = []
    for file in files:
        content = await file.read()
        try:
            doc = upload_uc.execute(project_id, file.filename, file.filename.split(".")[-1], content)
            responses.append(doc)
        except ValueError as e:
            # Skip invalid, continue batch
            continue
    return responses

# CHUNKED / RESUMABLE UPLOADS
@router.post("/chunk/init", response_model=ChunkUploadResponse)
def init_chunk_upload(
    filename: str = Form(...),
    total_chunks: int = Form(...),
    project_id: str = Depends(get_authenticated_project_id),
    db = Depends(get_db)
):
    """Initializes a chunked/resumable upload session."""
    upload_id = str(uuid.uuid4())
    upload = Upload(
        id=str(uuid.uuid4()),
        project_id=project_id,
        filename=filename,
        total_chunks=total_chunks,
        completed_chunks=0,
        upload_id=upload_id,
        status="pending",
        created_at=datetime.utcnow()
    )
    SQLUploadRepository(db).add(upload)
    return ChunkUploadResponse(
        upload_id=upload.upload_id,
        chunk_index=0,
        completed_chunks=0,
        total_chunks=total_chunks,
        status="pending"
    )

@router.post("/chunk/upload", response_model=DocumentResponse)
async def upload_chunk(
    upload_id: str = Form(...),
    chunk_index: int = Form(...),
    file: UploadFile = File(...),
    project_id: str = Depends(get_authenticated_project_id),
    db = Depends(get_db),
    upload_uc = Depends(get_document_use_cases)
):
    """
    Uploads a single chunk. Updates chunk progress.
    When all chunks are uploaded, merges them and registers the completed document.
    """
    up_repo = SQLUploadRepository(db)
    
    # Retrieve upload session
    upload_session = db.query(Upload).filter_by(upload_id=upload_id, project_id=project_id).first()
    # Direct query if mapping issue, let's query via SQLUploadRepository custom fetch if we had it,
    # or direct DB query:
    from src.infrastructure.database.models import UploadDB
    db_up = db.query(UploadDB).filter(UploadDB.upload_id == upload_id).first()
    if not db_up:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload session not found.")

    chunk_data = await file.read()
    
    # Save chunk to temp folder locally
    temp_dir = os.path.join(settings.STORAGE_LOCAL_DIR, "temp_chunks", upload_id)
    os.makedirs(temp_dir, exist_ok=True)
    
    chunk_file_path = os.path.join(temp_dir, f"part_{chunk_index}")
    with open(chunk_file_path, "wb") as f:
        f.write(chunk_data)
        
    # Update chunk status
    db_up.completed_chunks += 1
    
    if db_up.completed_chunks >= db_up.total_chunks:
        # Merge all chunks
        merged_content = bytearray()
        for idx in range(db_up.total_chunks):
            part_path = os.path.join(temp_dir, f"part_{idx}")
            if not os.path.exists(part_path):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing chunk index {idx}")
            with open(part_path, "rb") as pf:
                merged_content.extend(pf.read())
            # Clean up temp part file
            os.remove(part_path)
        
        # Clean up temp folder
        os.rmdir(temp_dir)
        
        # Save merged file
        db_up.status = "completed"
        db.commit()
        
        # Execute upload use case on merged content
        doc = upload_uc.execute(project_id, db_up.filename, db_up.filename.split(".")[-1], bytes(merged_content))
        return doc
    
    db.commit()
    # If not finished, return status as response (must match Pydantic schema or raise customized schema)
    # Since endpoint returns DocumentResponse on completion, let's return a temporary representation
    # or mock document schema details.
    # To satisfy FastAPIs response_model=DocumentResponse, let's raise a 202 Accepted status 
    # instead and return progress info.
    raise HTTPException(
        status_code=status.HTTP_202_ACCEPTED,
        detail=f"Chunk {chunk_index} received. Progress: {db_up.completed_chunks}/{db_up.total_chunks}"
    )

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    project_id: str = Depends(get_authenticated_project_id),
    db = Depends(get_db)
):
    doc_repo = SQLDocumentRepository(db)
    doc = doc_repo.get_by_id(document_id)
    if not doc or doc.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
        
    storage = get_storage_service()
    try:
        storage.delete_file(doc.file_path)
    except Exception:
        pass # Allow DB deletion even if storage clean fails
        
    doc_repo.delete(document_id)
    return None
