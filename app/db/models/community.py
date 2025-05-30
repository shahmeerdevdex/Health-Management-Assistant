from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from app.db.base import Base

class ModerationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"
    DELETED = "deleted"

class ReportSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SupportGroup(Base):
    __tablename__ = "support_groups"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    condition_tag = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_private = Column(Boolean, default=False)
    requires_approval = Column(Boolean, default=False)
    moderator_ids = Column(String, nullable=True)  # Comma-separated list of moderator user IDs
    rules = Column(Text, nullable=True)
    member_count = Column(Integer, default=0)

    posts = relationship("CommunityPost", back_populates="group", cascade="all, delete-orphan")
    members = relationship("GroupMembership", back_populates="group", cascade="all, delete-orphan")

class GroupMembership(Base):
    __tablename__ = "group_memberships"

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("support_groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String, default="member")  # member, moderator, admin
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="active")  # active, banned, pending

    group = relationship("SupportGroup", back_populates="members")
    user = relationship("User", back_populates="group_memberships")

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
    status = Column(Enum(ModerationStatus), default=ModerationStatus.PENDING)
    moderation_notes = Column(Text, nullable=True)
    moderated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    moderated_at = Column(DateTime(timezone=True), nullable=True)
    last_edited_at = Column(DateTime(timezone=True), nullable=True)
    edit_history = Column(Text, nullable=True)  # JSON string of edit history

    user = relationship("User", foreign_keys=[user_id], back_populates="community_posts")
    moderator = relationship("User", foreign_keys=[moderated_by])
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
    status = Column(Enum(ModerationStatus), default=ModerationStatus.PENDING)
    moderation_notes = Column(Text, nullable=True)
    moderated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    moderated_at = Column(DateTime(timezone=True), nullable=True)
    parent_comment_id = Column(Integer, ForeignKey("community_comments.id"), nullable=True)

    post = relationship("CommunityPost", back_populates="comments")
    user = relationship("User", foreign_keys=[user_id], back_populates="community_comments")
    moderator = relationship("User", foreign_keys=[moderated_by])
    parent = relationship("CommunityComment", remote_side=[id], backref="replies")

class CommunityLike(Base):
    __tablename__ = "community_likes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("community_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    post = relationship("CommunityPost", back_populates="likes")
    user = relationship("User", back_populates="community_likes")

class CommunityReport(Base):
    __tablename__ = "community_reports"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("community_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(Text, nullable=False)
    severity = Column(Enum(ReportSeverity), default=ReportSeverity.MEDIUM)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="pending")  # pending, reviewed, resolved
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    post = relationship("CommunityPost", back_populates="reports")
    user = relationship("User", foreign_keys=[user_id], back_populates="community_reports")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
