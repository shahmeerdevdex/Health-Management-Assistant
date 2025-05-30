from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_
from datetime import datetime
from typing import List, Optional
from fastapi import UploadFile, HTTPException
from app.db.models.referral import Referral, ReferralDocument, ReferralHistory
from app.db.models.user import User
from app.schemas.referral_system import ReferralStatus, ReferralPriority
from app.services.notification_service import send_notification
from app.services.document_storage import store_document, get_document_url

async def get_specialists_by_type(db: AsyncSession, specialist_type: str) -> List[User]:
    """Find available specialists of a specific type."""
    result = await db.execute(
        select(User)
        .join(User.practitioner_profile)
        .where(
            and_(
                User.practitioner_profile.specialization == specialist_type,
                User.practitioner_profile.is_available == True
            )
        )
    )
    return result.scalars().all()

async def attach_documents_to_referral(
    db: AsyncSession,
    referral_id: int,
    documents: List[UploadFile],
    practitioner_id: int
) -> dict:
    """Attach medical documents to a referral."""
    # Verify referral exists and practitioner has access
    referral = await db.execute(
        select(Referral).where(
            and_(
                Referral.id == referral_id,
                or_(
                    Referral.from_practitioner_id == practitioner_id,
                    Referral.to_practitioner_id == practitioner_id
                )
            )
        )
    )
    referral = referral.scalar_one_or_none()
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found or access denied")

    # Store documents and create document records
    document_ids = []
    for doc in documents:
        # Store document securely
        doc_url = await store_document(doc)
        
        # Create document record
        doc_record = ReferralDocument(
            referral_id=referral_id,
            document_url=doc_url,
            uploaded_by=practitioner_id,
            uploaded_at=datetime.utcnow()
        )
        db.add(doc_record)
        document_ids.append(doc_url)

    # Add to history
    history_entry = ReferralHistory(
        referral_id=referral_id,
        action="DOCUMENTS_ATTACHED",
        performed_by=practitioner_id,
        details=f"Attached {len(documents)} documents"
    )
    db.add(history_entry)

    await db.commit()
    return {"document_ids": document_ids}

async def schedule_appointment(
    db: AsyncSession,
    referral_id: int,
    appointment_date: datetime,
    practitioner_id: int
) -> dict:
    """Schedule an appointment for a referral."""
    # Convert timezone-aware datetime to timezone-naive UTC
    if appointment_date.tzinfo is not None:
        appointment_date = appointment_date.astimezone().replace(tzinfo=None)

    # Verify referral exists and practitioner has access
    referral = await db.execute(
        select(Referral).where(
            and_(
                Referral.id == referral_id,
                or_(
                    Referral.from_practitioner_id == practitioner_id,
                    Referral.to_practitioner_id == practitioner_id
                )
            )
        )
    )
    referral = referral.scalar_one_or_none()
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found or access denied")

    # Update referral with appointment date
    referral.appointment_date = appointment_date
    referral.status = ReferralStatus.IN_PROGRESS

    # Add to history
    history_entry = ReferralHistory(
        referral_id=referral_id,
        action="APPOINTMENT_SCHEDULED",
        performed_by=practitioner_id,
        details=f"Scheduled appointment for {appointment_date}"
    )
    db.add(history_entry)

    # Send notifications
    await send_notification(
        user_id=referral.from_practitioner_id,
        title="Appointment Scheduled",
        message=f"Appointment scheduled for referral #{referral_id} on {appointment_date}",
        notification_type="appointment"
    )
    await send_notification(
        user_id=referral.to_practitioner_id,
        title="Appointment Scheduled",
        message=f"Appointment scheduled for referral #{referral_id} on {appointment_date}",
        notification_type="appointment"
    )
    await send_notification(
        user_id=referral.patient_id,
        title="Appointment Scheduled",
        message=f"Your appointment has been scheduled for {appointment_date}",
        notification_type="appointment"
    )

    await db.commit()
    return {"appointment_date": appointment_date}

async def add_referral_feedback(
    db: AsyncSession,
    referral_id: int,
    feedback: str,
    practitioner_id: int
) -> dict:
    """Add feedback to a referral."""
    # Verify referral exists and practitioner has access
    referral = await db.execute(
        select(Referral).where(
            and_(
                Referral.id == referral_id,
                or_(
                    Referral.from_practitioner_id == practitioner_id,
                    Referral.to_practitioner_id == practitioner_id
                )
            )
        )
    )
    referral = referral.scalar_one_or_none()
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found or access denied")

    # Update referral with feedback
    referral.feedback = feedback

    # Add to history
    history_entry = ReferralHistory(
        referral_id=referral_id,
        action="FEEDBACK_ADDED",
        performed_by=practitioner_id,
        details="Added feedback to referral"
    )
    db.add(history_entry)

    # Notify other practitioner
    other_practitioner_id = (
        referral.to_practitioner_id if practitioner_id == referral.from_practitioner_id
        else referral.from_practitioner_id
    )
    await send_notification(
        user_id=other_practitioner_id,
        title="New Referral Feedback",
        message=f"New feedback added to referral #{referral_id}",
        notification_type="referral_feedback"
    )

    await db.commit()
    return {"feedback": feedback}

async def get_referral_workflow_history(
    db: AsyncSession,
    referral_id: int
) -> List[dict]:
    """Get the complete history of a referral."""
    # Get all history entries
    result = await db.execute(
        select(ReferralHistory)
        .where(ReferralHistory.referral_id == referral_id)
        .order_by(ReferralHistory.timestamp)
    )
    history_entries = result.scalars().all()

    # Get all documents
    doc_result = await db.execute(
        select(ReferralDocument)
        .where(ReferralDocument.referral_id == referral_id)
    )
    documents = doc_result.scalars().all()

    return {
        "history": [
            {
                "action": entry.action,
                "performed_by": entry.performed_by,
                "timestamp": entry.timestamp,
                "details": entry.details
            }
            for entry in history_entries
        ],
        "documents": [
            {
                "document_url": doc.document_url,
                "uploaded_by": doc.uploaded_by,
                "uploaded_at": doc.uploaded_at
            }
            for doc in documents
        ]
    }

async def send_referral_message(
    db: AsyncSession,
    referral_id: int,
    message: str,
    practitioner_id: int
) -> dict:
    """Send a message to the other practitioner involved in the referral."""
    # Verify referral exists and practitioner has access
    referral = await db.execute(
        select(Referral).where(
            and_(
                Referral.id == referral_id,
                or_(
                    Referral.from_practitioner_id == practitioner_id,
                    Referral.to_practitioner_id == practitioner_id
                )
            )
        )
    )
    referral = referral.scalar_one_or_none()
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found or access denied")

    # Determine recipient
    recipient_id = (
        referral.to_practitioner_id if practitioner_id == referral.from_practitioner_id
        else referral.from_practitioner_id
    )

    # Send notification
    await send_notification(
        user_id=recipient_id,
        title="New Referral Message",
        message=f"New message regarding referral #{referral_id}: {message}",
        notification_type="referral_message"
    )

    # Add to history
    history_entry = ReferralHistory(
        referral_id=referral_id,
        action="MESSAGE_SENT",
        performed_by=practitioner_id,
        details=message
    )
    db.add(history_entry)
    await db.commit()

    return {"message": message, "recipient_id": recipient_id} 