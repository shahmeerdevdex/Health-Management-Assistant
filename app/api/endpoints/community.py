from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from sqlalchemy.future import select
from app.schemas.community import (
    CommunityPostRequest, CommunityPostResponse, 
    CommunityCommentResponse, CommunityCommentRequest,
    CommunityLikeRequest, CommunityReportRequest,
    ModerationActionRequest, ModerationResponse,
    CommunityReportResponse
)
from app.db.models.community import (
    CommunityPost, CommunityComment, CommunityLike, CommunityReport,
    ModerationStatus, ReportSeverity
)
from app.services.moderation_service import ModerationService
from app.api.endpoints.dependencies import get_db, get_current_user
from app.db.models.user import User, UserRoleInput

router = APIRouter()

@router.post("/posts", response_model=CommunityPostResponse)
async def create_post(
    request: CommunityPostRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new community post."""
    # Initialize moderation service
    moderation_service = ModerationService(db)
    
    # Create post with pending status
    new_post = CommunityPost(
        user_id=current_user.id,
        title=request.title,
        content=request.content,
        category=request.category,
        is_anonymous=request.is_anonymous,
        status=ModerationStatus.PENDING
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    
    # Auto-approve if user is trusted (e.g., has been active for a while)
    if current_user.role in [UserRoleInput.PRACTITIONER, UserRoleInput.PROFESSIONAL]:
        await moderation_service.moderate_post(
            new_post.id,
            current_user.id,
            ModerationStatus.APPROVED,
            "Auto-approved for trusted user"
        )
    
    return new_post

@router.get("/posts", response_model=List[CommunityPostResponse])
async def get_all_posts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: Optional[ModerationStatus] = ModerationStatus.APPROVED
):
    """Fetch community posts with optional status filter."""
    query = select(CommunityPost).where(CommunityPost.status == status)
    posts = await db.execute(query.order_by(CommunityPost.created_at.desc()))
    return posts.scalars().all()

@router.get("/posts/{post_id}", response_model=CommunityPostResponse)
async def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch a specific post with comments."""
    post = await db.get(CommunityPost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check if user can view the post
    if post.status != ModerationStatus.APPROVED:
        moderation_service = ModerationService(db)
        is_moderator = await moderation_service.is_moderator(current_user.id)
        if not is_moderator and post.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Post not available")
    
    return post

@router.post("/posts/{post_id}/comment", response_model=CommunityCommentResponse)
async def add_comment(
    post_id: int,
    request: CommunityCommentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a comment to a post."""
    # Initialize moderation service
    moderation_service = ModerationService(db)
    
    # Create comment with pending status
    new_comment = CommunityComment(
        post_id=post_id,
        user_id=current_user.id,
        content=request.content,
        status=ModerationStatus.PENDING
    )
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)
    
    # Auto-approve if user is trusted
    if current_user.role in [UserRoleInput.PRACTITIONER, UserRoleInput.PROFESSIONAL]:
        await moderation_service.moderate_comment(
            new_comment.id,
            current_user.id,
            ModerationStatus.APPROVED,
            "Auto-approved for trusted user"
        )
    
    return new_comment

@router.post("/posts/{post_id}/like", response_model=CommunityLikeRequest)
async def like_post(post_id: int, db: Session = Depends(get_db), db_user=Depends(get_current_user)):
    """
    Like/upvote a post.
    """
    new_like = CommunityLike(
        post_id=post_id,
        user_id=db_user.id
    )
    db.add(new_like)
    await db.commit()
    await db.refresh(new_like)
    return {"post_id":post_id ,"message": "Post liked successfully"}

@router.post("/posts/{post_id}/report", response_model=CommunityReportResponse)
async def report_post(
    post_id: int,
    request: CommunityReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Report a post for moderation."""
    new_report = CommunityReport(
        post_id=post_id,
        user_id=current_user.id,
        reason=request.reason,
        severity=request.severity if hasattr(request, 'severity') else ReportSeverity.MEDIUM
    )
    db.add(new_report)
    await db.commit()
    await db.refresh(new_report)
    return new_report

@router.post("/moderate/post/{post_id}", response_model=ModerationResponse)
async def moderate_post(
    post_id: int,
    request: ModerationActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Moderate a post (moderator only)."""
    moderation_service = ModerationService(db)
    
    # Check if user is a moderator
    is_moderator = await moderation_service.is_moderator(current_user.id)
    if not is_moderator:
        raise HTTPException(status_code=403, detail="Not authorized to moderate")
    
    # Perform moderation
    try:
        post = await moderation_service.moderate_post(
            post_id,
            current_user.id,
            request.action,
            request.notes
        )
        return {
            "id": post.id,
            "status": post.status,
            "message": f"Post {post.id} has been {post.status}"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/moderate/comment/{comment_id}", response_model=ModerationResponse)
async def moderate_comment(
    comment_id: int,
    request: ModerationActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Moderate a comment (moderator only)."""
    moderation_service = ModerationService(db)
    
    # Check if user is a moderator
    is_moderator = await moderation_service.is_moderator(current_user.id)
    if not is_moderator:
        raise HTTPException(status_code=403, detail="Not authorized to moderate")
    
    # Perform moderation
    try:
        comment = await moderation_service.moderate_comment(
            comment_id,
            current_user.id,
            request.action,
            request.notes
        )
        return {
            "id": comment.id,
            "status": comment.status,
            "message": f"Comment {comment.id} has been {comment.status}"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/moderation/pending", response_model=Dict[str, List[Any]])
async def get_pending_moderation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all content pending moderation (moderator only)."""
    moderation_service = ModerationService(db)
    
    # Check if user is a moderator
    is_moderator = await moderation_service.is_moderator(current_user.id)
    if not is_moderator:
        raise HTTPException(status_code=403, detail="Not authorized to view moderation queue")
    
    # Get pending content
    pending_content = await moderation_service.get_pending_moderation()
    
    # Convert reports to response model
    if "reports" in pending_content:
        pending_content["reports"] = [
            CommunityReportResponse.from_orm(report) 
            for report in pending_content["reports"]
        ]
    
    return pending_content
