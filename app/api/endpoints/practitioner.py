from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.practitioner import PractitionerCreate, PractitionerResponse, PatientSummary
from app.schemas.referral_system import ReferralCreate, ReferralResponse, ReferralUpdate
from app.crud.practitioner import create_practitioner, get_practitioners
from app.crud.referral_system import create_referral, get_referral , get_referrals_for_practitioner, update_referral
from app.api.endpoints.dependencies import get_current_user
from app.db.models.user import UserRoleInput, User
from typing import List, Dict, Any
from app.db.models.health_diary import HealthDiary
from app.db.models.medication import Medication
from app.crud.analytics import get_provider_analytics
from app.schemas.messaging import MessageCreate, MessageResponse
from app.crud.messaging import create_message, get_messages_between_users, delete_message
from app.services.practitioner import verify_practitioner_with_ahpra
from app.services.health_monitor import AutomatedHealthMonitor
from datetime import datetime
from app.crud.referral import attach_documents_to_referral, schedule_appointment, add_referral_feedback, get_referral_workflow_history, send_referral_message
from app.schemas.specialist import SpecialistType
from fastapi import UploadFile
from app.services.notification_service import send_notification
from app.core.security import hash_password
from sqlalchemy.future import select
from app.db.models.practitioners import Practitioner
from app.db.models.practitioner_patient import practitioner_patient
from app.db.models.health_checkin import HealthCheckIn

router = APIRouter()

@router.post("/add", response_model=PractitionerResponse)
async def add_practitioner_endpoint(
    email: str,
    password: str,
    full_name: str,
    specialty: str,
    contact_info: str,
    registration_number: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new user with PRACTITIONER role and their practitioner profile.
    """
    # Check if user with email already exists
    existing_user = await db.execute(
        select(User).where(User.email == email)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists"
        )

    try:
        # TODO: Re-enable AHPRA verification after testing
        # # Verify practitioner registration with AHPRA
        # verification_result = verify_practitioner_with_ahpra(registration_number)
        # if not verification_result.get("verified", False):
        #     raise HTTPException(
        #         status_code=400,
        #         detail="Invalid or unverified practitioner registration number"
        #     )

        # Create new user with PRACTITIONER role
        new_user = User(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role=UserRoleInput.PRACTITIONER,
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(new_user)
        await db.flush()  # Flush to get the user ID

        # Create practitioner profile
        practitioner_data = PractitionerCreate(
            user_id=new_user.id,
            name=full_name,
            specialty=specialty,
            contact_info=contact_info,
            registration_number=registration_number
        )
        
        practitioner = await create_practitioner(db, practitioner_data)
        await db.commit()
        
        return practitioner
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create practitioner: {str(e)}"
        )

@router.get("/list", response_model=List[PractitionerResponse])
async def list_practitioners(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    practitioners = await get_practitioners(db)
    return practitioners

@router.get("/dashboard", response_model=Dict[str, Any])
async def practitioner_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Enhanced practitioner dashboard with real-time monitoring:
    - Patient summaries
    - Real-time health status
    - Critical alerts
    - AI insights
    - Risk assessments
    """
    if current_user.role != UserRoleInput.PRACTITIONER:
        raise HTTPException(status_code=403, detail="Only practitioners can access the dashboard.")

    # Properly load the practitioner profile using async query
    result = await db.execute(
        select(Practitioner).where(Practitioner.user_id == current_user.id)
    )
    practitioner = result.scalar_one_or_none()
    
    if not practitioner:
        raise HTTPException(status_code=404, detail="Practitioner profile not found")

    # Get patients using async query with correct column names
    result = await db.execute(
        select(practitioner_patient.c.patient_id)
        .where(practitioner_patient.c.practitioner_id == practitioner.id)
    )
    patient_ids = [row[0] for row in result.all()]
    
    # Get patient details
    result = await db.execute(
        select(User)
        .where(User.id.in_(patient_ids))
    )
    patients = result.scalars().all()

    # Get real-time monitoring data
    monitor = AutomatedHealthMonitor(db)
    monitoring_data = {
        "critical_alerts": [],
        "patient_status": [],
        "ai_insights": [],
        "risk_assessment": []
    }

    for patient in patients:
        # Get latest health check-in and analysis
        result = await db.execute(
            select(HealthCheckIn)
            .where(HealthCheckIn.user_id == patient.id)
            .order_by(HealthCheckIn.timestamp.desc())
            .limit(1)
        )
        latest_checkin = result.scalar_one_or_none()

        analysis = await monitor.analyze_health_patterns(patient.id, days=7)
        
        # Simplified monitoring data without AI insights
        patient_status = {
            "patient_id": patient.id,
            "name": patient.full_name,
            "latest_checkin": latest_checkin.timestamp if latest_checkin else None,
            "vital_signs": latest_checkin.health_metrics if latest_checkin else None,
            "risk_level": analysis.get("risk_level", "unknown"),
            "active_alerts": analysis.get("alerts", [])
        }

        # Add critical alerts if any
        if analysis.get("risk_level") == "high":
            monitoring_data["critical_alerts"].append({
                "patient_id": patient.id,
                "patient_name": patient.full_name,
                "alert_type": "high_risk",
                "details": analysis.get("risk_factors", []),
                "timestamp": datetime.utcnow()
            })

        # Add risk assessment
        monitoring_data["risk_assessment"].append({
            "patient_id": patient.id,
            "patient_name": patient.full_name,
            "risk_factors": analysis.get("risk_factors", []),
            "trends": analysis.get("trends", []),
            "recommendations": analysis.get("recommendations", [])
        })

        monitoring_data["patient_status"].append(patient_status)

    # Get provider analytics
    analytics = await get_provider_analytics(db=db, practitioner_id=practitioner.id)

    return {
        "monitoring": monitoring_data,
        "analytics": analytics,
        "total_patients": len(patients),
        "active_patients": len([p for p in patients if p.health_checkins and (datetime.utcnow() - p.health_checkins[-1].timestamp).days <= 7])
    }

@router.get("/analytics/overview")
async def practitioner_analytics_overview(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role != UserRoleInput.PRACTITIONER:
        raise HTTPException(status_code=403, detail="Only practitioners can access analytics.")

    await db.refresh(current_user, attribute_names=["practitioner_profile"])
    if not current_user.practitioner_profile:
      raise HTTPException(status_code=404, detail="Practitioner profile not found")

    return await get_provider_analytics(db=db, practitioner_id=current_user.practitioner_profile.id)


@router.post("/referrals/send", response_model=ReferralResponse)
async def send_referral(
    referral: ReferralCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role != UserRoleInput.PRACTITIONER:
        raise HTTPException(status_code=403, detail="Only practitioners can send referrals.")

    if referral.from_practitioner_id == referral.to_practitioner_id:
        raise HTTPException(status_code=400, detail="Cannot refer to yourself.")

    # Create a new ReferralCreate model with all required fields
    referral_data = ReferralCreate(
        **referral.dict(),
        updated_at=datetime.utcnow(),
        appointment_date=None,  # Will be set when appointment is scheduled
        feedback=None,  # Will be set when feedback is provided
        documents_attached=[]  # Will be updated when documents are attached
    )
    
    created_referral = await create_referral(db=db, referral=referral_data)
    
    # Convert to ReferralResponse format
    return ReferralResponse(
        id=created_referral.id,
        patient_id=created_referral.patient_id,
        from_practitioner_id=created_referral.from_practitioner_id,
        to_practitioner_id=created_referral.to_practitioner_id,
        specialist_type=created_referral.specialist_type,
        reason=created_referral.reason,
        priority=created_referral.priority,
        notes=created_referral.notes,
        status=created_referral.status,
        created_at=created_referral.created_at,
        updated_at=created_referral.updated_at,
        appointment_date=created_referral.appointment_date,
        feedback=created_referral.feedback,
        documents_attached=[],  # Empty list since no documents are attached yet
        workflow_history=[],  # Empty list since no history yet
        medical_history_required=created_referral.medical_history_required,
        test_results_required=created_referral.test_results_required
    )

@router.get("/referrals/my", response_model=List[ReferralResponse])
async def view_referrals(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role != UserRoleInput.PRACTITIONER:
        raise HTTPException(status_code=403, detail="Only practitioners can view referrals.")

    await db.refresh(current_user, attribute_names=["practitioner_profile"])
    if not current_user.practitioner_profile:
      raise HTTPException(status_code=404, detail="Practitioner profile not found")

    referrals = await get_referrals_for_practitioner(db=db, practitioner_id=current_user.practitioner_profile.id)
    
    # Convert Referral models to ReferralResponse format
    response_referrals = []
    for referral in referrals:
        response_referrals.append(
            ReferralResponse(
                id=referral.id,
                patient_id=referral.patient_id,
                from_practitioner_id=referral.from_practitioner_id,
                to_practitioner_id=referral.to_practitioner_id,
                specialist_type=referral.specialist_type,
                reason=referral.reason,
                priority=referral.priority,
                notes=referral.notes,
                status=referral.status,
                created_at=referral.created_at,
                updated_at=referral.updated_at,
                appointment_date=referral.appointment_date,
                feedback=referral.feedback,
                documents_attached=[doc.document_url for doc in referral.documents] if referral.documents else [],
                workflow_history=[],  # TODO: Implement workflow history
                medical_history_required=referral.medical_history_required,
                test_results_required=referral.test_results_required
            )
        )
    return response_referrals

@router.put("/referrals/update/{referral_id}", response_model=ReferralResponse)
async def update_referral_endpoint(
    referral_id: int,
    referral_update: ReferralUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role != UserRoleInput.PRACTITIONER:
        raise HTTPException(status_code=403, detail="Only practitioners can update referrals.")

    updated_referral = await update_referral(db=db, referral_id=referral_id, update_data=referral_update)
    if not updated_referral:
        raise HTTPException(status_code=404, detail="Referral not found")

    # Convert to ReferralResponse format
    return ReferralResponse(
        id=updated_referral.id,
        patient_id=updated_referral.patient_id,
        from_practitioner_id=updated_referral.from_practitioner_id,
        to_practitioner_id=updated_referral.to_practitioner_id,
        specialist_type=updated_referral.specialist_type,
        reason=updated_referral.reason,
        priority=updated_referral.priority,
        notes=updated_referral.notes,
        status=updated_referral.status,
        created_at=updated_referral.created_at,
        updated_at=updated_referral.updated_at,
        appointment_date=updated_referral.appointment_date,
        feedback=updated_referral.feedback,
        documents_attached=[doc.document_url for doc in updated_referral.documents] if updated_referral.documents else [],
        workflow_history=[],  # TODO: Implement workflow history
        medical_history_required=updated_referral.medical_history_required,
        test_results_required=updated_referral.test_results_required
    )

# Secure Messaging
@router.post("/send", response_model=MessageResponse)
async def send_message(
    message: MessageCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Send a secure, encrypted message between practitioners.
    Messages are encrypted at rest and in transit, with audit logging.
    """
    if current_user.role != UserRoleInput.PRACTITIONER:
        raise HTTPException(status_code=403, detail="Only practitioners can send messages.")

    return await create_message(
        db=db,
        sender_id=current_user.id,
        receiver_id=message.receiver_id,
        message_data=message,
        request=request
    )

@router.get("/chat/{receiver_id}", response_model=List[MessageResponse])
async def get_chat_messages(
    receiver_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Retrieve encrypted chat messages between practitioners.
    Messages are decrypted on retrieval and access is logged.
    """
    if current_user.role != UserRoleInput.PRACTITIONER:
        raise HTTPException(status_code=403, detail="Only practitioners can access messages.")

    return await get_messages_between_users(
        db=db,
        user_id=current_user.id,
        peer_id=receiver_id,
        request=request
    )

@router.delete("/message/{message_id}")
async def delete_message_endpoint(
    message_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Soft delete a message with audit logging.
    Messages are retained according to retention policy.
    """
    if current_user.role != UserRoleInput.PRACTITIONER:
        raise HTTPException(status_code=403, detail="Only practitioners can delete messages.")

    success = await delete_message(
        db=db,
        message_id=message_id,
        user_id=current_user.id,
        request=request
    )

    if not success:
        raise HTTPException(status_code=404, detail="Message not found or unauthorized to delete")

    return {"status": "success", "message": "Message deleted successfully"}

@router.get("/verify-practitioner/{registration_number}")
async def verify_practitioner(registration_number: str):
    """
    Verify a practitioner's AHPRA registration via PIE API.
    """
    try:
        result = verify_practitioner_with_ahpra(registration_number)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/monitoring/real-time", response_model=Dict[str, Any])
async def real_time_monitoring(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Real-time monitoring dashboard for practitioners:
    - Patient health diaries
    - Critical alerts
    - Risk assessment
    """
    if current_user.role != UserRoleInput.PRACTITIONER:
        raise HTTPException(status_code=403, detail="Only practitioners can access real-time monitoring.")

    # Properly load the practitioner profile using async query
    result = await db.execute(
        select(Practitioner).where(Practitioner.user_id == current_user.id)
    )
    practitioner = result.scalar_one_or_none()
    
    if not practitioner:
        raise HTTPException(status_code=404, detail="Practitioner profile not found")

    # Get patients using async query
    result = await db.execute(
        select(practitioner_patient.c.patient_id)
        .where(practitioner_patient.c.practitioner_id == practitioner.id)
    )
    patient_ids = [row[0] for row in result.all()]
    
    # Get patient details
    result = await db.execute(
        select(User)
        .where(User.id.in_(patient_ids))
    )
    patients = result.scalars().all()

    monitoring_data = {
        "critical_alerts": [],
        "patient_status": [],
        "risk_assessment": []
    }

    for patient in patients:
        # Get latest health check-in
        result = await db.execute(
            select(HealthCheckIn)
            .where(HealthCheckIn.user_id == patient.id)
            .order_by(HealthCheckIn.timestamp.desc())
            .limit(1)
        )
        latest_checkin = result.scalar_one_or_none()

        # Get health analysis
        monitor = AutomatedHealthMonitor(db)
        analysis = await monitor.analyze_health_patterns(patient.id, days=7)

        # Process patient status
        patient_status = {
            "patient_id": patient.id,
            "name": patient.full_name,
            "latest_checkin": latest_checkin.timestamp if latest_checkin else None,
            "vital_signs": latest_checkin.health_metrics if latest_checkin else None,
            "risk_level": analysis.get("risk_level", "unknown"),
            "active_alerts": analysis.get("alerts", [])
        }

        # Add critical alerts if any
        if analysis.get("risk_level") == "high":
            monitoring_data["critical_alerts"].append({
                "patient_id": patient.id,
                "patient_name": patient.full_name,
                "alert_type": "high_risk",
                "details": analysis.get("risk_factors", []),
                "timestamp": datetime.utcnow()
            })

        # Add risk assessment
        monitoring_data["risk_assessment"].append({
            "patient_id": patient.id,
            "patient_name": patient.full_name,
            "risk_factors": analysis.get("risk_factors", []),
            "trends": analysis.get("trends", []),
            "recommendations": analysis.get("recommendations", [])
        })

        monitoring_data["patient_status"].append(patient_status)

    return monitoring_data

@router.post("/referrals/{referral_id}/documents")
async def attach_referral_documents(
    referral_id: int,
    documents: List[UploadFile],
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Attach medical documents to a referral.
    Documents are securely stored and accessible to the receiving practitioner.
    """
    if current_user.role != UserRoleInput.PRACTITIONER:
        raise HTTPException(status_code=403, detail="Only practitioners can attach documents.")
    
    # TODO: Implement secure document storage and attachment
    return await attach_documents_to_referral(db, referral_id, documents, current_user.id)

@router.post("/referrals/{referral_id}/schedule")
async def schedule_referral_appointment(
    referral_id: int,
    appointment_date: datetime,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Schedule an appointment for a referral.
    Sends notifications to both practitioners and the patient.
    """
    if current_user.role != UserRoleInput.PRACTITIONER:
        raise HTTPException(status_code=403, detail="Only practitioners can schedule appointments.")
    
    # TODO: Implement appointment scheduling with notifications
    return await schedule_appointment(db, referral_id, appointment_date, current_user.id)

@router.post("/referrals/{referral_id}/feedback")
async def provide_referral_feedback(
    referral_id: int,
    feedback: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Provide feedback on a referral.
    Can be used by both referring and receiving practitioners.
    """
    if current_user.role != UserRoleInput.PRACTITIONER:
        raise HTTPException(status_code=403, detail="Only practitioners can provide feedback.")
    
    # TODO: Implement feedback system
    return await add_referral_feedback(db, referral_id, feedback, current_user.id)

@router.get("/referrals/{referral_id}/history")
async def get_referral_history(
    referral_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Get the complete history of a referral including all status changes,
    document attachments, and communications.
    """
    if current_user.role != UserRoleInput.PRACTITIONER:
        raise HTTPException(status_code=403, detail="Only practitioners can view referral history.")
    
    # TODO: Implement referral history tracking
    return await get_referral_workflow_history(db, referral_id)

@router.post("/referrals/{referral_id}/notify")
async def send_referral_notification(
    referral_id: int,
    message: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Send a notification to the other practitioner involved in the referral.
    """
    if current_user.role != UserRoleInput.PRACTITIONER:
        raise HTTPException(status_code=403, detail="Only practitioners can send notifications.")
    
    # TODO: Implement notification system
    return await send_referral_message(db, referral_id, message, current_user.id)