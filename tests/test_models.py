"""
Tests for SQLAlchemy database models and table initialization.
"""

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from app.database import Base, init_db
from app.models import (
    Image,
    ImageMetadata,
    BlogPost,
    ImageEmbedding,
    PostEmbedding,
    Suggestion,
    Review,
)


@pytest.fixture(scope="function")
def db_session():
    """Provides an isolated in-memory SQLite database session for model testing."""
    test_engine = create_engine("sqlite:///:memory:")
    init_db(target_engine=test_engine)

    TestSession = sessionmaker(bind=test_engine)
    session = TestSession()

    yield session, test_engine

    session.close()


def test_tables_exist(db_session):
    """Confirm all 7 required tables are created during initialization."""
    _, engine = db_session
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    expected_tables = {
        "images",
        "image_metadata",
        "blog_posts",
        "image_embeddings",
        "post_embeddings",
        "suggestions",
        "reviews",
    }

    assert expected_tables.issubset(table_names), f"Missing tables: {expected_tables - table_names}"


def test_repeated_initialization_is_safe(db_session):
    """Verify that calling init_db repeatedly does not raise errors (idempotence)."""
    _, engine = db_session
    # Second initialization run
    init_db(target_engine=engine)
    inspector = inspect(engine)
    assert "images" in inspector.get_table_names()


def test_insert_and_retrieve_sample_image(db_session):
    """Insert and retrieve a sample image along with its metadata and embedding."""
    session, _ = db_session

    sample_image = Image(
        filename="sunset_beach.jpg",
        file_path="images/sunset_beach.jpg",
        status="processed",
    )
    session.add(sample_image)
    session.commit()

    # Retrieve from DB
    retrieved = session.query(Image).filter_by(filename="sunset_beach.jpg").first()
    assert retrieved is not None
    assert retrieved.id is not None
    assert retrieved.status == "processed"
    assert retrieved.file_path == "images/sunset_beach.jpg"

    # Add metadata
    metadata = ImageMetadata(
        image_id=retrieved.id,
        subject="Tropical beach sunset with palm trees",
        category="Nature",
        attributes={"colors": ["orange", "purple"], "time_of_day": "sunset"},
        caption="A beautiful sunset overlooking a quiet beach shoreline.",
        confidence=0.96,
    )
    session.add(metadata)
    session.commit()

    # Add embedding (JSON format)
    dummy_vector = [0.12, -0.45, 0.88, 0.03]
    embedding = ImageEmbedding(
        image_id=retrieved.id,
        embedding=dummy_vector,
    )
    session.add(embedding)
    session.commit()

    # Verify relationships
    refreshed_image = session.query(Image).filter_by(id=retrieved.id).first()
    assert refreshed_image.image_metadata is not None
    assert refreshed_image.image_metadata.category == "Nature"
    assert refreshed_image.image_metadata.attributes["colors"] == ["orange", "purple"]
    assert refreshed_image.embedding.embedding == dummy_vector


def test_insert_and_retrieve_sample_blog_post(db_session):
    """Insert and retrieve a sample blog post along with post embedding."""
    session, _ = db_session

    sample_post = BlogPost(
        title="Top 10 Coastal Escapes for Summer",
        content="Here are the most breathtaking seaside getaways you must explore this year...",
        expected_subject="Beach Vacation",
    )
    session.add(sample_post)
    session.commit()

    # Retrieve from DB
    retrieved = session.query(BlogPost).filter_by(title="Top 10 Coastal Escapes for Summer").first()
    assert retrieved is not None
    assert retrieved.id is not None
    assert retrieved.expected_subject == "Beach Vacation"

    # Add embedding
    dummy_post_vector = [0.08, -0.32, 0.77, 0.15]
    post_emb = PostEmbedding(
        post_id=retrieved.id,
        embedding=dummy_post_vector,
    )
    session.add(post_emb)
    session.commit()

    # Verify relationship
    refreshed_post = session.query(BlogPost).filter_by(id=retrieved.id).first()
    assert refreshed_post.embedding is not None
    assert refreshed_post.embedding.embedding == dummy_post_vector


def test_suggestion_and_review_workflow(db_session):
    """Verify suggestion creation and human review approval/rejection."""
    session, _ = db_session

    # Create image and post
    image = Image(filename="mountain.png", file_path="images/mountain.png")
    post = BlogPost(title="Hiking in the Alps", content="Alpine trails offer stunning vistas.")
    session.add_all([image, post])
    session.commit()

    # Create match suggestion
    suggestion = Suggestion(
        post_id=post.id,
        image_id=image.id,
        similarity_score=0.91,
        status="pending",
        reason="High semantic alignment between hiking content and alpine mountains.",
    )
    session.add(suggestion)
    session.commit()

    assert suggestion.id is not None
    assert suggestion.post.title == "Hiking in the Alps"
    assert suggestion.image.filename == "mountain.png"

    # Human review decision
    review = Review(
        suggestion_id=suggestion.id,
        decision="approved",
    )
    session.add(review)
    session.commit()

    assert suggestion.review is not None
    assert suggestion.review.decision == "approved"
