from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from app.db.models.messaging import Message
from app.schemas.messaging import MessageCreate
from datetime import datetime
from typing import List


async def create_message(db: AsyncSession, sender_id: int, receiver_id: int, message_data: MessageCreate) -> Message:
    message = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=message_data.content,
        timestamp=datetime.utcnow(),
        is_read=False
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def get_messages_between_users(db: AsyncSession, user_id: int, peer_id: int) -> List[Message]:
    result = await db.execute(
        select(Message).where(
            or_(
                (Message.sender_id == user_id) & (Message.receiver_id == peer_id),
                (Message.sender_id == peer_id) & (Message.receiver_id == user_id)
            )
        ).order_by(Message.timestamp.desc())
    )
    return result.scalars().all()
