import uuid
from datetime import datetime
from src.infrastructure.queue.celery_app import celery_app
from src.infrastructure.database.session import get_db_context
from src.infrastructure.database.repositories import (
    SQLOCRJobRepository, SQLDocumentRepository, SQLOCRResultRepository, SQLExportRepository
)
from src.infrastructure.storage.service import get_storage_service
from src.infrastructure.ai.pipeline import OcrPipelineCoordinator
from src.infrastructure.exporters.service import generate_export_format
from src.domain.value_objects import OcrEngineConfig
from src.domain.entities.ocr_result import OCRResult
from src.domain.entities.export import Export
from src.config import settings

@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def process_ocr_job(self, job_id: str):
    """
    Asynchronous task to run a complete OCR pipeline process on a document.
    Updates DB status and progress as it runs.
    """
    db_gen = get_db_context()
    db = next(db_gen)
    
    job_repo = SQLOCRJobRepository(db)
    doc_repo = SQLDocumentRepository(db)
    result_repo = SQLOCRResultRepository(db)
    export_repo = SQLExportRepository(db)
    storage = get_storage_service()

    job = job_repo.get_by_id(job_id)
    if not job:
        db.close()
        return f"Job {job_id} not found."

    document = doc_repo.get_by_id(job.document_id)
    if not document:
        job.fail("Document metadata not found.")
        job_repo.update(job)
        db.close()
        return f"Document {job.document_id} not found."

    try:
        # Step 1: Downloading document
        job.update_progress(0.10, "DOWNLOADING")
        job_repo.update(job)
        
        file_bytes = storage.download_file(document.file_path)
        
        # Step 2: Set up pipeline config
        job.update_progress(0.20, "PREPROCESSING")
        job_repo.update(job)
        
        engine_name = job.engine_config.get("recognition_engine", settings.OCR_RECOGNITION_ENGINE)
        pipeline = OcrPipelineCoordinator(recognition_engine_name=engine_name)
        
        # Convert engine config dict to domain VO
        config_vo = OcrEngineConfig(
            recognition_engine=engine_name,
            detect_tables=job.engine_config.get("detect_tables", True),
            detect_forms=job.engine_config.get("detect_forms", True),
            language=job.engine_config.get("language", "en"),
            preprocessing_steps=job.engine_config.get("preprocessing_steps")
        )
        
        # Step 3: Run pipeline detection (LocateAnything)
        job.update_progress(0.40, "DETECTION")
        job_repo.update(job)
        
        # Step 4: Run OCR Recognition
        job.update_progress(0.60, "RECOGNITION")
        job_repo.update(job)
        
        # Step 5: Structuring & Post Processing
        job.update_progress(0.80, "POST_PROCESSING")
        job_repo.update(job)
        
        raw_text, structured_json, avg_conf = pipeline.run_pipeline(
            file_bytes, document.file_type, config_vo
        )
        
        # Add document info back into the final json
        structured_json["document_id"] = document.id
        
        # Step 6: Write OCR Results
        result_id = str(uuid.uuid4())
        ocr_result = OCRResult(
            id=result_id,
            job_id=job.id,
            document_id=document.id,
            raw_text=raw_text,
            structured_json=structured_json,
            confidence=avg_conf,
            created_at=datetime.utcnow()
        )
        result_repo.add(ocr_result)
        
        # Step 7: Export Generation (Default JSON and TXT exports uploaded to storage)
        job.update_progress(0.90, "EXPORT_GENERATION")
        job_repo.update(job)
        
        # Export default formats (JSON and TXT)
        for fmt in ["JSON", "TXT"]:
            exp_bytes = generate_export_format(structured_json, fmt)
            dest_path = f"exports/{job.id}/{document.name}.{fmt.lower()}"
            uploaded_path = storage.upload_file(exp_bytes, dest_path)
            
            export_entity = Export(
                id=str(uuid.uuid4()),
                job_id=job.id,
                format=fmt,
                file_path=uploaded_path,
                created_at=datetime.utcnow()
            )
            export_repo.add(export_entity)
            
        # Complete Job
        job.complete()
        job_repo.update(job)
        
        # Update Document status
        document.update_status("completed")
        doc_repo.update(document)
        
    except Exception as exc:
        # Handle Retry / Failure
        db.rollback()
        logger.error(f"Error processing job {job_id}: {str(exc)}", exc_info=True)
        try:
            self.retry(exc=exc)
        except Exception:
            # Max retries reached or un-retryable error
            job.fail(str(exc))
            job_repo.update(job)
            document.update_status("failed")
            doc_repo.update(document)
            
    finally:
        db.close()
