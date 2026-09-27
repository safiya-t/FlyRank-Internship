"""
Automated unit tests for Gemini image understanding integration in app/ai.py.
All Gemini API interactions are mocked to avoid external calls, costs, and rate limits.
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from app.ai import (
    analyze_image,
    ImageValidationError,
    AIConfigurationError,
    AIModelError,
    InvalidAIResponseError,
)
from app.config import settings

SAMPLE_IMAGE_PATH = "images/sample.png"


def create_mock_response(text: str, prompt_tokens: int = 120, candidate_tokens: int = 45):
    """Helper to construct a mock Gemini response."""
    mock_resp = MagicMock()
    mock_resp.text = text
    mock_usage = MagicMock()
    mock_usage.prompt_token_count = prompt_tokens
    mock_usage.candidates_token_count = candidate_tokens
    mock_usage.total_token_count = prompt_tokens + candidate_tokens
    mock_resp.usage_metadata = mock_usage
    return mock_resp


# ==========================================
# 1. Valid Structured Output Test
# ==========================================

def test_analyze_image_valid_output():
    """Verify that a valid model JSON response is parsed into ImageAnalysisResult."""
    valid_payload = {
        "subject": "Green mountain landscape under clear sky",
        "category": "Nature",
        "attributes": ["mountain", "sun", "sky", "green hills"],
        "caption": "A scenic landscape featuring rolling green hills with a bright yellow sun.",
        "confidence": 0.95,
    }
    mock_resp = create_mock_response(json.dumps(valid_payload))

    with patch.object(settings, "GEMINI_API_KEY", "test-api-key"), \
         patch("app.ai.genai.Client") as mock_client_cls:

        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.models.generate_content.return_value = mock_resp

        result = analyze_image(
            image_path=SAMPLE_IMAGE_PATH,
            model_name="gemini-2.5-flash",
            confidence_threshold=0.70,
        )

        assert result.metadata.subject == valid_payload["subject"]
        assert result.metadata.category == "Nature"
        assert result.metadata.confidence == 0.95
        assert len(result.metadata.attributes) == 4
        assert result.flagged is False
        assert result.flag_reason is None

        # Verify processing info tracking
        assert result.processing_info.model == "gemini-2.5-flash"
        assert result.processing_info.timestamp is not None
        assert result.processing_info.usage["prompt_token_count"] == 120
        assert result.processing_info.usage["candidates_token_count"] == 45


# ==========================================
# 2. Malformed JSON Test
# ==========================================

def test_analyze_image_rejects_malformed_json():
    """Verify that non-JSON or syntax-broken model outputs raise InvalidAIResponseError."""
    broken_payload = "This is not valid JSON { subject: 'incomplete' ... "
    mock_resp = create_mock_response(broken_payload)

    with patch.object(settings, "GEMINI_API_KEY", "test-api-key"), \
         patch("app.ai.genai.Client") as mock_client_cls:

        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.models.generate_content.return_value = mock_resp

        with pytest.raises(InvalidAIResponseError) as exc_info:
            analyze_image(SAMPLE_IMAGE_PATH)

        assert "not valid JSON" in str(exc_info.value)


# ==========================================
# 3. Missing Fields and Invalid Types Test
# ==========================================

def test_analyze_image_rejects_missing_required_fields():
    """Verify that model outputs missing mandatory fields (subject, category, caption) are rejected."""
    incomplete_payload = {
        "category": "Nature",
        "attributes": ["sun"],
        # Missing 'subject', 'caption', 'confidence'
    }
    mock_resp = create_mock_response(json.dumps(incomplete_payload))

    with patch.object(settings, "GEMINI_API_KEY", "test-api-key"), \
         patch("app.ai.genai.Client") as mock_client_cls:

        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.models.generate_content.return_value = mock_resp

        with pytest.raises(InvalidAIResponseError) as exc_info:
            analyze_image(SAMPLE_IMAGE_PATH)

        assert "validation" in str(exc_info.value).lower()


def test_analyze_image_rejects_empty_string_fields():
    """Verify that empty or whitespace-only subject/caption are rejected."""
    blank_field_payload = {
        "subject": "   ",
        "category": "Nature",
        "attributes": [],
        "caption": "Valid caption",
        "confidence": 0.85,
    }
    mock_resp = create_mock_response(json.dumps(blank_field_payload))

    with patch.object(settings, "GEMINI_API_KEY", "test-api-key"), \
         patch("app.ai.genai.Client") as mock_client_cls:

        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.models.generate_content.return_value = mock_resp

        with pytest.raises(InvalidAIResponseError) as exc_info:
            analyze_image(SAMPLE_IMAGE_PATH)

        assert "cannot be empty" in str(exc_info.value).lower()


# ==========================================
# 4. Low Confidence Flagging Test
# ==========================================

def test_analyze_image_flags_low_confidence():
    """Verify that confidence below threshold produces a flagged result with reason."""
    low_conf_payload = {
        "subject": "Blurry outdoor scene",
        "category": "Unknown",
        "attributes": ["blur", "unclear"],
        "caption": "An ambiguous image where the subject cannot be clearly identified.",
        "confidence": 0.42,
    }
    mock_resp = create_mock_response(json.dumps(low_conf_payload))

    with patch.object(settings, "GEMINI_API_KEY", "test-api-key"), \
         patch("app.ai.genai.Client") as mock_client_cls:

        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.models.generate_content.return_value = mock_resp

        result = analyze_image(
            image_path=SAMPLE_IMAGE_PATH,
            confidence_threshold=0.70,
        )

        assert result.flagged is True
        assert result.flag_reason is not None
        assert "below configured threshold" in result.flag_reason
        assert result.metadata.confidence == 0.42


# ==========================================
# 5. Invalid Image Handling Test
# ==========================================

def test_analyze_image_missing_file():
    """Verify ImageValidationError when the target file does not exist."""
    with patch.object(settings, "GEMINI_API_KEY", "test-api-key"):
        with pytest.raises(ImageValidationError) as exc_info:
            analyze_image("images/non_existent_image_123.jpg")
        assert "does not exist" in str(exc_info.value)


# ==========================================
# 6. Missing API Key Test
# ==========================================

def test_analyze_image_missing_api_key():
    """Verify AIConfigurationError when GEMINI_API_KEY is blank or missing."""
    with patch.object(settings, "GEMINI_API_KEY", ""):
        with pytest.raises(AIConfigurationError) as exc_info:
            analyze_image(SAMPLE_IMAGE_PATH)
        assert "GEMINI_API_KEY is not configured" in str(exc_info.value)


# ==========================================
# 7. No Invention of Usage Data Test
# ==========================================

def test_analyze_image_preserves_none_usage():
    """Verify usage is None if Gemini response provides no usage_metadata."""
    payload = {
        "subject": "Mountain",
        "category": "Nature",
        "attributes": ["peak"],
        "caption": "Snow-capped peak.",
        "confidence": 0.90,
    }
    mock_resp = MagicMock()
    mock_resp.text = json.dumps(payload)
    mock_resp.usage_metadata = None  # No usage metadata provided

    with patch.object(settings, "GEMINI_API_KEY", "test-api-key"), \
         patch("app.ai.genai.Client") as mock_client_cls:

        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.models.generate_content.return_value = mock_resp

        result = analyze_image(SAMPLE_IMAGE_PATH)
        assert result.processing_info.usage is None
