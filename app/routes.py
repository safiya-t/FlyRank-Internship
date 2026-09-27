"""
API endpoint route handlers for image upload, batch processing, and job status.
"""

import io
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from PIL import Image as PILImage, UnidentifiedImageError

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Depends,
    HTTPException,
    BackgroundTasks,
    Query,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.models import Image, ImageMetadata
from app.ai import analyze_image, AIModelError, AIError
from app.schemas import (
    ImageUploadResponse,
    JobCreateResponse,
    JobStatusResponse,
    JobDetailItem,
)

router = APIRouter()

# Constraints
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB limit
MAX_RETRIES = 3  # Retry policy for transient model errors

# In-memory storage for local background job tracking
# In production, this would typically reside in Redis or a persistent database table
jobs_store: Dict[str, Dict[str, Any]] = {}


# ==========================================
# Background Processing Worker
# ==========================================

def run_batch_image_processing(
    job_id: str,
    image_ids: List[int],
    max_retries: int = MAX_RETRIES,
) -> None:
    """
    Background worker that iterates through target images, calls Gemini vision analysis,
    validates structured metadata, applies retries on transient errors, and records metrics.
    """
    job = jobs_store.get(job_id)
    if not job:
        return

    job["status"] = "processing"
    db: Session = SessionLocal()

    try:
        for img_id in image_ids:
            img = db.query(Image).filter(Image.id == img_id).first()
            if not img:
                continue

            # Mark current image status as processing
            img.status = "processing"
            db.commit()

            attempts = 0
            analysis_result = None
            last_error = None

            # Retry policy for transient errors (up to max_retries attempts)
            while attempts < max_retries:
                attempts += 1
                try:
                    analysis_result = analyze_image(img.file_path)
                    break
                except (AIModelError, AIError) as exc:
                    last_error = str(exc)
                    if attempts < max_retries:
                        time.sleep(0.5 * attempts)  # Incremental backoff
                except Exception as exc:
                    last_error = str(exc)
                    break  # Non-retryable error

            if analysis_result:
                final_status = "flagged" if analysis_result.flagged else "completed"
                img.status = final_status

                # Upsert metadata in ImageMetadata table
                meta_record = db.query(ImageMetadata).filter(ImageMetadata.image_id == img.id).first()
                if not meta_record:
                    meta_record = ImageMetadata(image_id=img.id)
                    db.add(meta_record)

                meta_record.subject = analysis_result.metadata.subject
                meta_record.category = analysis_result.metadata.category
                meta_record.caption = analysis_result.metadata.caption
                meta_record.confidence = analysis_result.metadata.confidence
                meta_record.attributes = {
                    "tags": analysis_result.metadata.attributes,
                    "processing_info": analysis_result.processing_info.model_dump(),
                    "flag_reason": analysis_result.flag_reason,
                }
                db.commit()

                # Update job counters
                job["processed_images"] += 1
                if analysis_result.flagged:
                    job["flagged_images"] += 1
                else:
                    job["successful_images"] += 1

                job["details"].append(
                    JobDetailItem(
                        image_id=img.id,
                        filename=img.filename,
                        status=final_status,
                        retries=attempts - 1,
                        usage=analysis_result.processing_info.usage,
                    )
                )
            else:
                img.status = "failed"
                db.commit()

                job["processed_images"] += 1
                job["failed_images"] += 1
                job["details"].append(
                    JobDetailItem(
                        image_id=img.id,
                        filename=img.filename,
                        status="failed",
                        retries=attempts - 1,
                        error=last_error,
                    )
                )

        job["status"] = "completed"
        job["completed_at"] = datetime.now(timezone.utc).isoformat()

    except Exception as exc:
        job["status"] = "failed"
        job["completed_at"] = datetime.now(timezone.utc).isoformat()
    finally:
        db.close()


# ==========================================
# Endpoints
# ==========================================

@router.post(
    "/images/upload",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Images"],
)
def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Accepts an uploaded image file (JPEG, PNG, WebP), validates file integrity and size,
    saves it safely to images/ with a unique filename, and records it in PostgreSQL.
    """
    filename = file.filename or "image.png"
    ext = os.path.splitext(filename)[1].lower()

    # 1. Validate file extension
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # 2. Validate MIME type header
    if file.content_type and file.content_type.lower() not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid MIME type '{file.content_type}'. Allowed types: {', '.join(sorted(ALLOWED_MIME_TYPES))}",
        )

    # 3. Read content and enforce maximum file size
    try:
        content = file.file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read uploaded file: {exc}",
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum limit of {MAX_FILE_SIZE // (1024 * 1024)}MB.",
        )

    # 4. Validate image binary using Pillow to ensure valid, uncorrupted image
    try:
        with PILImage.open(io.BytesIO(content)) as test_img:
            test_img.verify()
            img_format = test_img.format.upper() if test_img.format else ""
            if img_format not in {"JPEG", "PNG", "WEBP"}:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Decoded image format '{img_format}' is not supported.",
                )
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Corrupted or invalid image file: {exc}",
        )

    # 5. Save to images/ folder with safe, collision-proof filename
    os.makedirs("images", exist_ok=True)
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join("images", unique_filename).replace("\\", "/")

    with open(file_path, "wb") as disk_file:
        disk_file.write(content)

    # 6. Save image record in PostgreSQL
    image_record = Image(
        filename=os.path.basename(filename),
        file_path=file_path,
        status="pending",
    )
    db.add(image_record)
    db.commit()
    db.refresh(image_record)

    return image_record


@router.post(
    "/jobs/process-images",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Jobs"],
)
def start_batch_processing(
    background_tasks: BackgroundTasks,
    response: Response,
    force_reprocess: bool = Query(
        default=False,
        description="If True, reprocess images that are already marked completed or flagged.",
    ),
    db: Session = Depends(get_db),
):
    """
    Initiates background image analysis on unprocessed images.
    Safe against redundant calls: completed images are skipped unless force_reprocess is True.
    """
    # Select images that require processing
    if force_reprocess:
        query = db.query(Image)
    else:
        query = db.query(Image).filter(Image.status.in_(["pending", "failed"]))

    target_images = query.all()
    image_ids = [img.id for img in target_images]

    if not image_ids:
        response.status_code = status.HTTP_200_OK
        return JobCreateResponse(
            job_id="none",
            status="completed",
            total_images=0,
            message="No images currently require processing. Set force_reprocess=true to rerun completed images.",
        )

    job_id = str(uuid.uuid4())
    jobs_store[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "total_images": len(image_ids),
        "processed_images": 0,
        "successful_images": 0,
        "failed_images": 0,
        "flagged_images": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "details": [],
    }

    # Dispatch to FastAPI background task worker
    background_tasks.add_task(run_batch_image_processing, job_id, image_ids)

    return JobCreateResponse(
        job_id=job_id,
        status="processing",
        total_images=len(image_ids),
        message=f"Batch processing started in background for {len(image_ids)} image(s).",
    )


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    tags=["Jobs"],
)
def get_job_status(job_id: str):
    """
    Returns progress, status counts (successful, failed, flagged), and per-image details for a job.
    """
    job = jobs_store.get(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found.",
        )

    return JobStatusResponse(**job)
