"""
Gemini integration for image understanding and structured metadata extraction.
Uses the official google-genai Python SDK with Gemini Flash.
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional
from PIL import Image, UnidentifiedImageError
from pydantic import ValidationError

from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.config import settings
from app.schemas import (
    ImageMetadataSchema,
    ProcessingMetadata,
    ImageAnalysisResult,
)


class AIError(Exception):
    """Base exception for all AI processing errors."""
    pass


class ImageValidationError(AIError):
    """Raised when an image file does not exist, cannot be opened, or is corrupted."""
    pass


class AIConfigurationError(AIError):
    """Raised when API credentials or required settings are missing."""
    pass


class AIModelError(AIError):
    """Raised when the Gemini API service encounters an error or fails to respond."""
    pass


class InvalidAIResponseError(AIError):
    """Raised when the model output is malformed, unparseable, or violates schema."""
    pass


PROMPT_IMAGE_UNDERSTANDING = """
Analyze the provided image and extract structured understanding in JSON format matching the schema:
- subject: Primary subject of the image (concise description)
- category: High-level classification category (e.g. Nature, Architecture, Technology, People, Food, Travel, etc.)
- attributes: List of relevant visual tags, descriptive keywords, and attributes (e.g. ["sunset", "beach", "orange sky"])
- caption: A detailed, clear caption describing the full visual scene
- confidence: Numerical confidence score between 0.0 and 1.0 reflecting visual clarity and certainty of the analysis
"""


def _load_image_safely(image_path: str) -> Image.Image:
    """
    Safely opens and validates an image file using Pillow.
    Guards against corrupted, missing, or malicious files.
    """
    if not os.path.exists(image_path):
        raise ImageValidationError(f"Image file does not exist: {image_path}")

    try:
        # First verify file integrity
        with Image.open(image_path) as test_img:
            test_img.verify()

        # Reopen after verify (verify closes/invalidates the file descriptor)
        image = Image.open(image_path)
        image.load()
        return image
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ImageValidationError(f"Cannot open or decode image at '{image_path}': {exc}")


def analyze_image(
    image_path: str,
    model_name: Optional[str] = None,
    confidence_threshold: Optional[float] = None,
) -> ImageAnalysisResult:
    """
    Analyzes an image using Google's Gemini Flash model and returns validated structured metadata.

    Args:
        image_path: Path to the local image file.
        model_name: Optional override for the vision model name (defaults to GEMINI_VISION_MODEL).
        confidence_threshold: Optional override for minimum confidence threshold.

    Returns:
        ImageAnalysisResult: Validated metadata, flag status, and per-call processing info.

    Raises:
        ImageValidationError: If the image cannot be read or is invalid.
        AIConfigurationError: If GEMINI_API_KEY is not configured.
        AIModelError: If the Gemini API request fails.
        InvalidAIResponseError: If the model returns malformed JSON or invalid schema values.
    """
    # 1. Validate API Key configuration without exposing the key in logs
    api_key = settings.GEMINI_API_KEY
    if not api_key or not api_key.strip():
        raise AIConfigurationError("GEMINI_API_KEY is not configured. Please set it in your .env file.")

    effective_model = model_name or settings.GEMINI_VISION_MODEL
    effective_threshold = (
        confidence_threshold if confidence_threshold is not None else settings.CONFIDENCE_THRESHOLD
    )

    # 2. Open image safely
    pil_image = _load_image_safely(image_path)

    # 3. Initialize Gemini Client
    try:
        client = genai.Client(api_key=api_key)
    except Exception as exc:
        raise AIConfigurationError(f"Failed to initialize Gemini Client: {exc}")

    # 4. Configure structured JSON generation
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=ImageMetadataSchema,
        temperature=0.2,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )

    # 5. Invoke Gemini Flash Model
    try:
        response = client.models.generate_content(
            model=effective_model,
            contents=[pil_image, PROMPT_IMAGE_UNDERSTANDING],
            config=config,
        )
    except APIError as exc:
        raise AIModelError(f"Gemini API error during image analysis: {exc.message}")
    except Exception as exc:
        raise AIModelError(f"Unexpected error calling Gemini model '{effective_model}': {exc}")

    # 6. Extract raw response text
    raw_text = getattr(response, "text", None)
    if not raw_text or not raw_text.strip():
        raise InvalidAIResponseError("Gemini model returned an empty response.")

    # 7. Parse JSON - reject malformed responses
    try:
        parsed_data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise InvalidAIResponseError(f"Model response is not valid JSON: {exc}. Raw text: {raw_text[:200]}")

    if not isinstance(parsed_data, dict):
        raise InvalidAIResponseError(f"Expected JSON object from model, got: {type(parsed_data).__name__}")

    # 8. Validate against Pydantic schema - do not trust model output
    try:
        validated_metadata = ImageMetadataSchema.model_validate(parsed_data)
    except ValidationError as exc:
        raise InvalidAIResponseError(f"Model output failed schema validation: {exc}")

    # 9. Confidence threshold guard check
    is_flagged = validated_metadata.confidence < effective_threshold
    flag_reason = None
    if is_flagged:
        flag_reason = (
            f"Confidence score {validated_metadata.confidence:.2f} is below configured threshold of {effective_threshold:.2f}."
        )

    # 10. Extract per-call processing info without inventing usage data
    usage_dict: Optional[dict[str, int]] = None
    if hasattr(response, "usage_metadata") and response.usage_metadata is not None:
        usage = response.usage_metadata
        temp_usage: dict[str, int] = {}
        if getattr(usage, "prompt_token_count", None) is not None:
            temp_usage["prompt_token_count"] = usage.prompt_token_count
        if getattr(usage, "candidates_token_count", None) is not None:
            temp_usage["candidates_token_count"] = usage.candidates_token_count
        if getattr(usage, "total_token_count", None) is not None:
            temp_usage["total_token_count"] = usage.total_token_count
        if temp_usage:
            usage_dict = temp_usage

    processing_info = ProcessingMetadata(
        model=effective_model,
        timestamp=datetime.now(timezone.utc).isoformat(),
        usage=usage_dict,
    )

    return ImageAnalysisResult(
        metadata=validated_metadata,
        flagged=is_flagged,
        flag_reason=flag_reason,
        processing_info=processing_info,
    )
