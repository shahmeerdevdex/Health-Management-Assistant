from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy.future import select
from app.schemas.community import (
    CommunityPostRequest, CommunityPostResponse, 
    CommunityCommentResponse,CommunityCommentRequest,
    CommunityLikeRequest, CommunityReportRequest
)
from app.db.models.community import CommunityPost, CommunityComment, CommunityLike, CommunityReport
from app.api.endpoints.dependencies import get_db, get_current_user

router = APIRouter()

@router.post("/posts", response_model=CommunityPostResponse)
async def create_post(request: CommunityPostRequest, db: Session = Depends(get_db), db_user=Depends(get_current_user)):
    """
    Create a new community post.
    """
    new_post = CommunityPost(
        user_id=db_user.id,
        title=request.title,
        content=request.content,
        category=request.category,
        is_anonymous=request.is_anonymous
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    return new_post

@router.get("/posts", response_model=List[CommunityPostResponse])
async def get_all_posts(db: Session = Depends(get_db), db_user=Depends(get_current_user)):
    """
    Fetch all community posts.
    """
    posts = await db.execute(select(CommunityPost).order_by(CommunityPost.created_at.desc()))
    return posts.scalars().all()

@router.get("/posts/{post_id}", response_model=CommunityPostResponse)
async def get_post(post_id: int, db: Session = Depends(get_db),db_user=Depends(get_current_user)):
    """
    Fetch a specific post with comments.
    """
    post = await db.get(CommunityPost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@router.post("/posts/{post_id}/comment", response_model=CommunityCommentResponse)
async def add_comment(post_id: int, request: CommunityCommentRequest, db: Session = Depends(get_db), db_user=Depends(get_current_user)):
    """
    Add a comment to a post.
    """
    new_comment = CommunityComment(
        post_id=post_id,
        user_id=db_user.id,
        content=request.content
    )
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)
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

@router.post("/posts/{post_id}/report", response_model=CommunityReportRequest)
async def report_post(post_id: int, request: CommunityReportRequest, db: Session = Depends(get_db), db_user=Depends(get_current_user)):
    """
    Report a post for moderation.
    """
    new_report = CommunityReport(
        post_id=post_id,
        user_id=db_user.id,
        reason=request.reason
    )
    db.add(new_report)
    await db.commit()
    await db.refresh(new_report)
    return {"post_id": post_id, "reason": request.reason, "message": "Post reported successfully"}
