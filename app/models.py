"""
SQLAlchemy ORM models for AI Image Understanding & Content Matching Engine.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Image(Base):
    """
    Represents an uploaded image asset.
    File data is stored in the file system (images/ directory); only metadata & paths are stored here.
    """
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    status = Column(String(50), default="uploaded", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    image_metadata = relationship(
        "ImageMetadata",
        back_populates="image",
        uselist=False,
        cascade="all, delete-orphan",
    )
    embedding = relationship(
        "ImageEmbedding",
        back_populates="image",
        uselist=False,
        cascade="all, delete-orphan",
    )
    suggestions = relationship(
        "Suggestion",
        back_populates="image",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Image id={self.id} filename='{self.filename}' status='{self.status}'>"


class ImageMetadata(Base):
    """
    Extracted AI understanding metadata for an image (subject, tags, caption, confidence).
    """
    __tablename__ = "image_metadata"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(
        Integer,
        ForeignKey("images.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    subject = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True, index=True)
    attributes = Column(JSON, nullable=True)  # Key-value tags, colors, detected entities
    caption = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    image = relationship("Image", back_populates="image_metadata")

    def __repr__(self) -> str:
        return f"<ImageMetadata id={self.id} image_id={self.image_id} category='{self.category}'>"


class BlogPost(Base):
    """
    Represents a blog post or article that requires relevant image matching.
    """
    __tablename__ = "blog_posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    expected_subject = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    embedding = relationship(
        "PostEmbedding",
        back_populates="post",
        uselist=False,
        cascade="all, delete-orphan",
    )
    suggestions = relationship(
        "Suggestion",
        back_populates="post",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<BlogPost id={self.id} title='{self.title}'>"


class ImageEmbedding(Base):
    """
    Vector embedding representing an image, stored as JSON for lightweight semantic matching.
    """
    __tablename__ = "image_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(
        Integer,
        ForeignKey("images.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    embedding = Column(JSON, nullable=False)  # List of floating-point values

    # Relationships
    image = relationship("Image", back_populates="embedding")

    def __repr__(self) -> str:
        return f"<ImageEmbedding id={self.id} image_id={self.image_id}>"


class PostEmbedding(Base):
    """
    Vector embedding representing a blog post, stored as JSON for semantic comparison.
    """
    __tablename__ = "post_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(
        Integer,
        ForeignKey("blog_posts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    embedding = Column(JSON, nullable=False)  # List of floating-point values

    # Relationships
    post = relationship("BlogPost", back_populates="embedding")

    def __repr__(self) -> str:
        return f"<PostEmbedding id={self.id} post_id={self.post_id}>"


class Suggestion(Base):
    """
    Matches between blog posts and images produced by the semantic matching engine.
    """
    __tablename__ = "suggestions"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(
        Integer,
        ForeignKey("blog_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    image_id = Column(
        Integer,
        ForeignKey("images.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    similarity_score = Column(Float, nullable=False)
    status = Column(String(50), default="pending", nullable=False, index=True)  # pending, reviewed
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    post = relationship("BlogPost", back_populates="suggestions")
    image = relationship("Image", back_populates="suggestions")
    review = relationship(
        "Review",
        back_populates="suggestion",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Suggestion id={self.id} post_id={self.post_id} image_id={self.image_id} score={self.similarity_score}>"


class Review(Base):
    """
    Human review decisions (approved/rejected) on match suggestions.
    """
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    suggestion_id = Column(
        Integer,
        ForeignKey("suggestions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    decision = Column(String(50), nullable=False)  # "approved" or "rejected"
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    suggestion = relationship("Suggestion", back_populates="review")

    def __repr__(self) -> str:
        return f"<Review id={self.id} suggestion_id={self.suggestion_id} decision='{self.decision}'>"
