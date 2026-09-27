"""
Unit tests for Pydantic schema validation rules.
"""

import pytest
from pydantic import ValidationError

from app.schemas import (
    ImageUploadResponse,
    ImageMetadataSchema,
    BlogPostCreate,
    BlogPostResponse,
    ImageMatchResponse,
    SuggestionItem,
    ReviewCreate,
    ReviewResponse,
)


# ==========================================
# 1. ImageMetadataSchema Tests
# ==========================================

def test_valid_image_metadata():
    """Verify that valid image metadata passes validation."""
    data = {
        "subject": "Golden retriever puppy playing in the grass",
        "category": "Animals",
        "attributes": ["dog", "puppy", "golden retriever", "outdoor", "grass"],
        "caption": "A cute golden retriever puppy running happily across a green lawn.",
        "confidence": 0.95,
    }
    metadata = ImageMetadataSchema(**data)
    assert metadata.subject == data["subject"]
    assert metadata.category == "Animals"
    assert metadata.confidence == 0.95
    assert len(metadata.attributes) == 5


def test_image_metadata_rejects_confidence_out_of_range():
    """Verify that confidence < 0 or > 1 is rejected."""
    base_data = {
        "subject": "Landscape",
        "category": "Nature",
        "attributes": ["trees"],
        "caption": "Pine forest on a misty morning.",
    }

    # Too high (> 1.0)
    with pytest.raises(ValidationError) as exc_info:
        ImageMetadataSchema(**base_data, confidence=1.2)
    assert "confidence" in str(exc_info.value)

    # Negative (< 0.0)
    with pytest.raises(ValidationError) as exc_info:
        ImageMetadataSchema(**base_data, confidence=-0.1)
    assert "confidence" in str(exc_info.value)


def test_image_metadata_rejects_empty_strings():
    """Verify that whitespace-only or empty strings are rejected."""
    with pytest.raises(ValidationError):
        ImageMetadataSchema(
            subject="   ",
            category="Nature",
            attributes=[],
            caption="Valid caption",
            confidence=0.8,
        )


# ==========================================
# 2. BlogPostCreate Tests
# ==========================================

def test_valid_blog_post_create():
    """Verify valid blog post payload is accepted and whitespace is stripped."""
    post = BlogPostCreate(
        title="  Introduction to Fast Vector Search  ",
        content="  Learn how vector embeddings accelerate semantic retrieval.  ",
        expected_subject="Artificial Intelligence",
    )
    assert post.title == "Introduction to Fast Vector Search"
    assert post.content == "Learn how vector embeddings accelerate semantic retrieval."
    assert post.expected_subject == "Artificial Intelligence"


def test_blog_post_rejects_empty_title():
    """Verify that empty or whitespace-only title is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        BlogPostCreate(title="   ", content="Some valid content.")
    assert "title" in str(exc_info.value)


def test_blog_post_rejects_empty_content():
    """Verify that empty or whitespace-only content is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        BlogPostCreate(title="Valid Title", content="")
    assert "content" in str(exc_info.value)


# ==========================================
# 3. ImageMatchResponse Tests
# ==========================================

def test_image_match_response():
    """Verify matching response with nested suggestions."""
    data = {
        "post_id": 42,
        "suggestions": [
            {
                "image_id": 101,
                "caption": "A sunset over the mountains",
                "similarity_score": 0.89,
                "guard_status": "pass",
                "explanation": "Strong semantic similarity between mountain hiking and mountain image.",
            }
        ],
    }
    match_resp = ImageMatchResponse(**data)
    assert match_resp.post_id == 42
    assert len(match_resp.suggestions) == 1
    assert match_resp.suggestions[0].similarity_score == 0.89
    assert match_resp.suggestions[0].guard_status == "pass"


# ==========================================
# 4. ReviewCreate Tests
# ==========================================

def test_valid_review_decisions():
    """Verify that only 'approved' or 'rejected' are allowed."""
    rev_approved = ReviewCreate(decision="approved")
    assert rev_approved.decision == "approved"

    rev_rejected = ReviewCreate(decision="rejected")
    assert rev_rejected.decision == "rejected"


def test_invalid_review_decision():
    """Verify that any decision other than 'approved' or 'rejected' is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        ReviewCreate(decision="maybe")
    assert "Input should be 'approved' or 'rejected'" in str(exc_info.value)
