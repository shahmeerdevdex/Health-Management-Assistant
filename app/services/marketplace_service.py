from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from app.schemas.marketplace import (
    MentalHealthMarketplaceRequest,
    MentalHealthMarketplaceResponse,
    MentalHealthProfessional
)
from app.db.models.appointments import Appointment
from app.db.models.mental_health import Professional
from utils.payment import process_payment
from utils.video_call_link import generate_video_call_link
from datetime import datetime

async def process_mental_health_marketplace(request: MentalHealthMarketplaceRequest, db: Session) -> MentalHealthMarketplaceResponse:
    """
    Fetches available mental health professionals or books an appointment.
    """
    if request.action == "search":
        # Fetch professionals from the database instead of using mock data
        query = select(Professional).where(
            (request.location is None or Professional.location == request.location),
            (request.specialties is None or Professional.specialty.in_(request.specialties)),
            (request.insurance_coverage is False or Professional.accepts_insurance),
            (request.online_consultation is False or Professional.online_available)
        )
        result = await db.execute(query)
        professionals = result.scalars().all()

        message = f"Found {len(professionals)} professionals matching your criteria."
        return MentalHealthMarketplaceResponse(
            user_id=request.user_id,
            available_professionals=professionals,
            message=message
        )

    elif request.action == "book":
        # Ensure therapist ID and time slot are provided
        if not request.therapist_id or not request.preferred_time:
            raise HTTPException(status_code=400, detail="Therapist ID and preferred time required for booking.")

        # Process payment if required
        if request.payment_required:
            payment_status = await process_payment(request.user_id, request.therapist_id, request.payment_details)
            if not payment_status["success"]:
                raise HTTPException(status_code=402, detail="Payment failed.")

        # Create an appointment
        appointment = Appointment(
            user_id=request.user_id,
            therapist_id=request.therapist_id,
            date_time=request.preferred_time,
            status="Confirmed"
        )
        db.add(appointment)
        await db.commit()
        await db.refresh(appointment)

        # Generate a secure video call link
        video_call_link = await generate_video_call_link(request.therapist_id, request.preferred_time)

        return {
            "message": "Appointment booked successfully",
            "appointment": {
                "therapist_id": request.therapist_id,
                "date_time": request.preferred_time,
                "video_call_link": video_call_link
            }
        }

    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'search' or 'book'.")
