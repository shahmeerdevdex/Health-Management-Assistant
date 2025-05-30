from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_, update
from app.db.models.messaging import Message, MessageAuditLog
from app.schemas.messaging import MessageCreate, MessageAuditLogCreate
from datetime import datetime, timedelta
from typing import List, Optional
from app.services.encryption_service import encryption_service
from fastapi import Request
import logging

logger = logging.getLogger("messaging_crud")

async def create_message(
    db: AsyncSession,
    sender_id: int,
    receiver_id: int,
    message_data: MessageCreate,
    request: Optional[Request] = None
) -> Message:
    """Create a new encrypted message with audit logging."""
    try:
        # Encrypt message content
        encrypted_content = encryption_service.encrypt_message(message_data.content)
        
        # Create message
        message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=encrypted_content,
            message_type=message_data.message_type,
            retention_period=message_data.retention_period,
            message_metadata=message_data.meta_data,
            is_encrypted=True,
            timestamp=datetime.utcnow()
        )
        
        db.add(message)
        await db.commit()
        await db.refresh(message)
        
        # Create audit log
        if request:
            audit_log = MessageAuditLog(
                message_id=message.id,
                user_id=sender_id,
                action="create",
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                additional_info={"message_type": message_data.message_type}
            )
            db.add(audit_log)
            await db.commit()
        
        return message
    except Exception as e:
        logger.error(f"Error creating message: {str(e)}")
        raise

async def get_messages_between_users(
    db: AsyncSession,
    user_id: int,
    peer_id: int,
    request: Optional[Request] = None
) -> List[Message]:
    """Get messages between two users with decryption and audit logging."""
    try:
        result = await db.execute(
            select(Message).where(
                and_(
                    or_(
                        (Message.sender_id == user_id) & (Message.receiver_id == peer_id),
                        (Message.sender_id == peer_id) & (Message.receiver_id == user_id)
                    ),
                    Message.deleted_at.is_(None)
                )
            ).order_by(Message.timestamp.desc())
        )
        messages = result.scalars().all()
        
        # Decrypt messages
        for message in messages:
            if message.is_encrypted:
                message.content = encryption_service.decrypt_message(message.content)
            
            # Create audit log for message access
            if request:
                audit_log = MessageAuditLog(
                    message_id=message.id,
                    user_id=user_id,
                    action="read",
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent")
                )
                db.add(audit_log)
        
        await db.commit()
        return messages
    except Exception as e:
        logger.error(f"Error retrieving messages: {str(e)}")
        raise

async def delete_message(
    db: AsyncSession,
    message_id: int,
    user_id: int,
    request: Optional[Request] = None
) -> bool:
    """Soft delete a message with audit logging."""
    try:
        result = await db.execute(
            select(Message).where(
                and_(
                    Message.id == message_id,
                    or_(Message.sender_id == user_id, Message.receiver_id == user_id)
                )
            )
        )
        message = result.scalars().first()
        
        if not message:
            return False
        
        # Soft delete
        message.deleted_at = datetime.utcnow()
        
        # Create audit log
        if request:
            audit_log = MessageAuditLog(
                message_id=message_id,
                user_id=user_id,
                action="delete",
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
            db.add(audit_log)
        
        await db.commit()
        return True
    except Exception as e:
        logger.error(f"Error deleting message: {str(e)}")
        raise

async def cleanup_expired_messages(db: AsyncSession) -> int:
    """Clean up messages that have exceeded their retention period."""
    try:
        current_time = datetime.utcnow()
        result = await db.execute(
            select(Message).where(
                and_(
                    Message.deleted_at.is_(None),
                    Message.timestamp + timedelta(days=Message.retention_period) < current_time
                )
            )
        )
        expired_messages = result.scalars().all()
        
        for message in expired_messages:
            message.deleted_at = current_time
            
            # Create audit log for automatic deletion
            audit_log = MessageAuditLog(
                message_id=message.id,
                user_id=message.sender_id,  # Use sender as the system user
                action="auto_delete",
                additional_info={"reason": "retention_period_expired"}
            )
            db.add(audit_log)
        
        await db.commit()
        return len(expired_messages)
    except Exception as e:
        logger.error(f"Error cleaning up expired messages: {str(e)}")
        raise
