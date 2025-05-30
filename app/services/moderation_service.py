from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.db.models.community import (
    CommunityPost, CommunityComment, CommunityReport,
    ModerationStatus, ReportSeverity, GroupMembership
)
from app.db.models.user import User

class ModerationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def moderate_post(
        self,
        post_id: int,
        moderator_id: int,
        action: ModerationStatus,
        notes: Optional[str] = None
    ) -> CommunityPost:
        """Moderate a community post."""
        post = await self._get_post(post_id)
        if not post:
            raise ValueError(f"Post {post_id} not found")

        # Update post status
        post.status = action
        post.moderation_notes = notes
        post.moderated_by = moderator_id
        post.moderated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(post)
        return post

    async def moderate_comment(
        self,
        comment_id: int,
        moderator_id: int,
        action: ModerationStatus,
        notes: Optional[str] = None
    ) -> CommunityComment:
        """Moderate a community comment."""
        comment = await self._get_comment(comment_id)
        if not comment:
            raise ValueError(f"Comment {comment_id} not found")

        # Update comment status
        comment.status = action
        comment.moderation_notes = notes
        comment.moderated_by = moderator_id
        comment.moderated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(comment)
        return comment

    async def handle_report(
        self,
        report_id: int,
        reviewer_id: int,
        resolution: str,
        notes: Optional[str] = None
    ) -> CommunityReport:
        """Handle a community report."""
        report = await self._get_report(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")

        # Update report status
        report.status = "resolved"
        report.reviewed_by = reviewer_id
        report.reviewed_at = datetime.utcnow()
        report.resolution_notes = notes

        # If report is valid, moderate the content
        if resolution == "valid":
            if report.post_id:
                await self.moderate_post(
                    report.post_id,
                    reviewer_id,
                    ModerationStatus.FLAGGED,
                    f"Content flagged due to report: {report.reason}"
                )

        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def get_pending_moderation(self) -> Dict[str, List[Any]]:
        """Get all content pending moderation."""
        # Get pending posts
        pending_posts = await self.db.execute(
            select(CommunityPost)
            .where(CommunityPost.status == ModerationStatus.PENDING)
            .order_by(CommunityPost.created_at.desc())
        )
        posts = pending_posts.scalars().all()

        # Get pending comments
        pending_comments = await self.db.execute(
            select(CommunityComment)
            .where(CommunityComment.status == ModerationStatus.PENDING)
            .order_by(CommunityComment.created_at.desc())
        )
        comments = pending_comments.scalars().all()

        # Get pending reports
        pending_reports = await self.db.execute(
            select(CommunityReport)
            .where(CommunityReport.status == "pending")
            .order_by(CommunityReport.created_at.desc())
        )
        reports = pending_reports.scalars().all()

        return {
            "posts": posts,
            "comments": comments,
            "reports": reports
        }

    async def is_moderator(self, user_id: int, group_id: Optional[int] = None) -> bool:
        """Check if a user is a moderator."""
        if group_id:
            # Check group-specific moderation
            membership = await self.db.execute(
                select(GroupMembership)
                .where(
                    (GroupMembership.user_id == user_id) &
                    (GroupMembership.group_id == group_id) &
                    (GroupMembership.role.in_(["moderator", "admin"]))
                )
            )
            return bool(membership.scalar_one_or_none())
        else:
            # Check global moderation (you might want to add a global moderator role to User model)
            user = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = user.scalar_one_or_none()
            return user and user.role == "ADMIN"  # Assuming ADMIN role has global moderation rights

    async def _get_post(self, post_id: int) -> Optional[CommunityPost]:
        """Get a post by ID."""
        result = await self.db.execute(
            select(CommunityPost).where(CommunityPost.id == post_id)
        )
        return result.scalar_one_or_none()

    async def _get_comment(self, comment_id: int) -> Optional[CommunityComment]:
        """Get a comment by ID."""
        result = await self.db.execute(
            select(CommunityComment).where(CommunityComment.id == comment_id)
        )
        return result.scalar_one_or_none()

    async def _get_report(self, report_id: int) -> Optional[CommunityReport]:
        """Get a report by ID."""
        result = await self.db.execute(
            select(CommunityReport).where(CommunityReport.id == report_id)
        )
        return result.scalar_one_or_none() 