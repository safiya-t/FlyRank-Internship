"""
Integration and unit tests for image upload and background job processing routes.
"""

import io
import json
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image as PILImage
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db, Base
from app.models import Image, ImageMetadata
from app.ai import (
    AIModelError,
    ImageAnalysisResult,
    ImageMetadataSchema,
    ProcessingMetadata,
)
from app.routes import jobs_store
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Setup in-memory test DB with StaticPool so all threads share the exact same database
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def create_test_image_bytes(fmt="PNG", size=(50, 50), color="blue"):
    """Generates valid image bytes in memory."""
    buf = io.BytesIO()
    img = PILImage.new("RGB", size, color=color)
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf.getvalue()


@pytest.fixture(autouse=True)
def clean_db():
    """Ensure a clean database state and session patch before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    jobs_store.clear()
    with patch("app.routes.SessionLocal", new=TestSession):
        yield


# ==========================================
# 1. Image Upload Tests
# ==========================================

def test_upload_valid_image():
    """Verify uploading a valid PNG file returns 201 and persists record in DB."""
    img_bytes = create_test_image_bytes(fmt="PNG")
    response = client.post(
        "/images/upload",
        files={"file": ("test_pic.png", img_bytes, "image/png")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "test_pic.png"
    assert data["status"] == "pending"
    assert "images/" in data["file_path"]

    # Verify persisted in DB
    db = TestSession()
    db_img = db.query(Image).filter_by(id=data["id"]).first()
    assert db_img is not None
    assert db_img.filename == "test_pic.png"
    db.close()


def test_upload_invalid_file_extension():
    """Verify rejection of files with invalid extensions."""
    response = client.post(
        "/images/upload",
        files={"file": ("notes.txt", b"plain text content", "text/plain")},
    )
    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["detail"]


def test_upload_corrupted_image():
    """Verify rejection of files with image extension but corrupt binary content."""
    response = client.post(
        "/images/upload",
        files={"file": ("fake.png", b"this is not a valid png", "image/png")},
    )
    assert response.status_code == 400
    assert "Corrupted or invalid image" in response.json()["detail"]


# ==========================================
# 2. Batch Processing & AI Analysis Tests
# ==========================================

def make_analysis_result(subject="Mountain", confidence=0.92, flagged=False):
    return ImageAnalysisResult(
        metadata=ImageMetadataSchema(
            subject=subject,
            category="Nature",
            attributes=["scenic", "outdoor"],
            caption=f"A scenic view of {subject}.",
            confidence=confidence,
        ),
        flagged=flagged,
        flag_reason="Confidence below threshold" if flagged else None,
        processing_info=ProcessingMetadata(
            model="gemini-2.5-flash",
            timestamp="2026-09-27T12:00:00Z",
            usage={"prompt_token_count": 100, "candidates_token_count": 50, "total_token_count": 150},
        ),
    )


def test_batch_processing_workflow():
    """Verify batch processing several images, metadata persistence, and job status."""
    db = TestSession()
    img1 = Image(filename="nature1.png", file_path="images/sample.png", status="pending")
    img2 = Image(filename="nature2.png", file_path="images/sample.png", status="pending")
    db.add_all([img1, img2])
    db.commit()
    img1_id = img1.id
    img2_id = img2.id
    db.close()

    mock_result = make_analysis_result("Sunny Hill", confidence=0.95, flagged=False)

    with patch("app.routes.analyze_image", return_value=mock_result):
        response = client.post("/jobs/process-images")
        assert response.status_code == 202
        job_data = response.json()
        job_id = job_data["job_id"]
        assert job_data["total_images"] == 2

        # Check job status via GET /jobs/{job_id}
        status_resp = client.get(f"/jobs/{job_id}")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        assert status_data["status"] == "completed"
        assert status_data["processed_images"] == 2
        assert status_data["successful_images"] == 2
        assert len(status_data["details"]) == 2

    # Verify metadata saved in database
    db = TestSession()
    saved_meta = db.query(ImageMetadata).filter_by(image_id=img1_id).first()
    assert saved_meta is not None
    assert saved_meta.subject == "Sunny Hill"
    assert saved_meta.category == "Nature"
    assert saved_meta.confidence == 0.95
    assert "processing_info" in saved_meta.attributes
    assert saved_meta.attributes["processing_info"]["usage"]["total_token_count"] == 150
    db.close()


def test_simulate_failed_ai_call_and_retries():
    """Verify retry behavior when transient AIModelError occurs."""
    db = TestSession()
    img = Image(filename="retry_img.png", file_path="images/sample.png", status="pending")
    db.add(img)
    db.commit()
    db.close()

    call_count = 0

    def mock_flaky_analyze(path):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise AIModelError(f"Transient network glitch attempt {call_count}")
        return make_analysis_result("Recovered Subject", confidence=0.90)

    with patch("app.routes.analyze_image", side_effect=mock_flaky_analyze), \
         patch("time.sleep", return_value=None):

        response = client.post("/jobs/process-images")
        job_id = response.json()["job_id"]

        status_resp = client.get(f"/jobs/{job_id}")
        status_data = status_resp.json()
        assert status_data["successful_images"] == 1
        assert status_data["details"][0]["retries"] == 2
        assert call_count == 3


def test_low_confidence_flagged_image():
    """Verify that images analyzed with low confidence are marked 'flagged'."""
    db = TestSession()
    img = Image(filename="blurry.png", file_path="images/sample.png", status="pending")
    db.add(img)
    db.commit()
    img_id = img.id
    db.close()

    mock_flagged_result = make_analysis_result("Blurry Shape", confidence=0.45, flagged=True)

    with patch("app.routes.analyze_image", return_value=mock_flagged_result):
        response = client.post("/jobs/process-images")
        job_id = response.json()["job_id"]

        status_resp = client.get(f"/jobs/{job_id}")
        status_data = status_resp.json()
        assert status_data["flagged_images"] == 1
        assert status_data["successful_images"] == 0
        assert status_data["details"][0]["status"] == "flagged"

    # Verify status in database
    db = TestSession()
    db_img = db.query(Image).filter_by(id=img_id).first()
    assert db_img.status == "flagged"
    assert db_img.image_metadata.attributes["flag_reason"] is not None
    db.close()


def test_repeated_job_requests_safe():
    """Verify that already completed images are skipped unless force_reprocess is specified."""
    db = TestSession()
    img = Image(filename="done.png", file_path="images/sample.png", status="completed")
    db.add(img)
    db.commit()
    db.close()

    # Without force_reprocess -> no images to process
    response = client.post("/jobs/process-images?force_reprocess=false")
    assert response.status_code == 200
    assert response.json()["total_images"] == 0
    assert "No images currently require processing" in response.json()["message"]


def test_job_not_found():
    """Verify 404 when querying an unknown job ID."""
    response = client.get("/jobs/non-existent-job-id-999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
