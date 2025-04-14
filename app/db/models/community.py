from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.db.base import Base

class SupportGroup(Base):
    __tablename__ = "support_groups"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    condition_tag = Column(String, nullable=False)
    description = Column(String)

    posts = relationship("CommunityPost", back_populates="group", cascade="all, delete-orphan")


class CommunityPost(Base):
    __tablename__ = "community_posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    is_anonymous = Column(Boolean, default=False)
    group_id = Column(Integer, ForeignKey("support_groups.id"), nullable=True, index=True)
    status = Column(String, default="active")  # e.g., "active", "flagged", "deleted"

    user = relationship("User", back_populates="community_posts")
    group = relationship("SupportGroup", back_populates="posts")
    comments = relationship("CommunityComment", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("CommunityLike", back_populates="post", cascade="all, delete-orphan")
    reports = relationship("CommunityReport", back_populates="post", cascade="all, delete-orphan")


class CommunityComment(Base):
    __tablename__ = "community_comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("community_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    post = relationship("CommunityPost", back_populates="comments")
    user = relationship("User", back_populates="community_comments")


class CommunityLike(Base):
    __tablename__ = "community_likes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("community_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    post = relationship("CommunityPost", back_populates="likes")
    user = relationship("User", back_populates="community_likes")


class CommunityReport(Base):
    __tablename__ = "community_reports"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("community_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    post = relationship("CommunityPost", back_populates="reports")
    user = relationship("User", back_populates="community_reports")
