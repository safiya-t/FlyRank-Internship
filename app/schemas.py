"""
Pydantic schemas for data validation and API serialization.
"""

from datetime import datetime
from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field, field_validator, ConfigDict


# ==========================================
# 1. Image Upload Schemas
# ==========================================

class ImageUploadResponse(BaseModel):
    """Response returned upon successful image upload."""
    id: int
    filename: str
    file_path: str
    status: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 2. Image Metadata Schemas
# ==========================================

class ImageMetadataSchema(BaseModel):
    """AI-extracted understanding and descriptive metadata for an image."""
    subject: str = Field(..., min_length=1, description="Primary subject of the image")
    category: str = Field(..., min_length=1, description="Classification category")
    attributes: List[str] = Field(default_factory=list, description="Visual attributes and tags")
    caption: str = Field(..., min_length=1, description="Detailed descriptive caption")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0",
    )

    @field_validator("subject", "category", "caption")
    @classmethod
    def check_not_blank(cls, v: str, info) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError(f"'{info.field_name}' cannot be empty or contain only whitespace.")
        return stripped

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 3. Blog Post Schemas
# ==========================================

class BlogPostCreate(BaseModel):
    """Request payload for creating a new blog post."""
    title: str = Field(..., min_length=1, max_length=255, description="Blog post title")
    content: str = Field(..., min_length=1, description="Full article content")
    expected_subject: Optional[str] = Field(None, max_length=255, description="Expected subject topic")

    @field_validator("title", "content")
    @classmethod
    def check_not_empty_or_whitespace(cls, v: str, info) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError(f"'{info.field_name}' cannot be empty or contain only whitespace.")
        return stripped

    @field_validator("expected_subject")
    @classmethod
    def clean_expected_subject(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            stripped = v.strip()
            return stripped if stripped else None
        return None


class BlogPostResponse(BaseModel):
    """Response schema for a persisted blog post."""
    id: int
    title: str
    content: str
    expected_subject: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 4. Image Matching Schemas
# ==========================================

class SuggestionItem(BaseModel):
    """An individual matched image suggestion for a blog post."""
    image_id: int
    caption: str
    similarity_score: float = Field(..., description="Semantic similarity score")
    guard_status: str = Field(..., description="Guardrail check status (e.g. 'pass', 'flagged')")
    explanation: str = Field(..., description="Reason for matching")

    model_config = ConfigDict(from_attributes=True)


class ImageMatchResponse(BaseModel):
    """Response payload for image matching against a blog post."""
    post_id: int
    suggestions: List[SuggestionItem] = Field(default_factory=list, description="List of image match suggestions")

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 5. Review Schemas
# ==========================================

class ReviewCreate(BaseModel):
    """Request payload for submitting a human review decision."""
    decision: Literal["approved", "rejected"] = Field(
        ...,
        description="Review decision: must be either 'approved' or 'rejected'",
    )


class ReviewResponse(BaseModel):
    """Response payload for a recorded human review."""
    id: int
    suggestion_id: int
    decision: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 6. AI Analysis Tracking Schemas
# ==========================================

class ProcessingMetadata(BaseModel):
    """Per-call processing information such as model, timestamp, and token usage."""
    model: str
    timestamp: str
    usage: Optional[Dict[str, int]] = None

    model_config = ConfigDict(from_attributes=True)


class ImageAnalysisResult(BaseModel):
    """Validated result of an image analysis call with guard flagging."""
    metadata: ImageMetadataSchema
    flagged: bool = False
    flag_reason: Optional[str] = None
    processing_info: ProcessingMetadata

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 7. Job Processing Schemas
# ==========================================

class JobDetailItem(BaseModel):
    """Execution status and metrics for an individual image within a job."""
    image_id: int
    filename: str
    status: str
    retries: int = 0
    error: Optional[str] = None
    usage: Optional[Dict[str, int]] = None

    model_config = ConfigDict(from_attributes=True)


class JobCreateResponse(BaseModel):
    """Response returned when initiating an image processing batch job."""
    job_id: str
    status: str
    total_images: int
    message: str

    model_config = ConfigDict(from_attributes=True)


class JobStatusResponse(BaseModel):
    """Current progress and detailed results of a background image processing job."""
    job_id: str
    status: str
    total_images: int
    processed_images: int
    successful_images: int
    failed_images: int
    flagged_images: int
    created_at: str
    completed_at: Optional[str] = None
    details: List[JobDetailItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

