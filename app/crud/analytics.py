from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime, timedelta
from app.db.models.practitioners import Practitioner
from app.db.models.user import User
from app.db.models.health_diary import HealthDiary
from app.db.models.medication import Medication
from app.db.models.practitioner_patient import practitioner_patient

async def get_provider_analytics(db: AsyncSession, practitioner_id: int):
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)

    # Step 1: Get all linked patient IDs
    result = await db.execute(
        select(User.id).select_from(practitioner_patient)
        .join(User, practitioner_patient.c.patient_id == User.id)
        .where(practitioner_patient.c.practitioner_id == practitioner_id)
    )
    patient_ids = [row[0] for row in result.fetchall()]
    if not patient_ids:
        return {
            "total_patients": 0,
            "active_patients_last_7_days": 0,
            "common_symptoms": [],
            "adherence_rate": 0.0,
            "missing_logs": []
        }

    # Step 2: Active patients with diary entries in the last 7 days
    result = await db.execute(
        select(func.count(func.distinct(HealthDiary.user_id)))
        .where(
            HealthDiary.user_id.in_(patient_ids),
            HealthDiary.date >= week_ago
        )
    )
    active_patients = result.scalar() or 0

    # Step 3: Common symptoms
    result = await db.execute(
        select(HealthDiary.symptoms)
        .where(
            HealthDiary.user_id.in_(patient_ids),
            HealthDiary.date >= week_ago,
            HealthDiary.symptoms.isnot(None)
        )
    )
    from collections import Counter
    all_symptoms = []
    for row in result.fetchall():
        if row[0]:
            all_symptoms.extend([s.strip().lower() for s in row[0].split(",")])
    common_symptoms = [sym for sym, _ in Counter(all_symptoms).most_common(5)]

    # Step 4: Medication adherence
    result = await db.execute(
        select(Medication.user_id)
        .where(
            Medication.user_id.in_(patient_ids),
            Medication.start_date <= today,
            (Medication.end_date.is_(None) | (Medication.end_date >= today))
        )
    )
    meds_taken = result.scalars().all()
    adherence_rate = round(len(set(meds_taken)) / len(patient_ids) * 100, 2) if patient_ids else 0.0

    # Step 5: Patients who didn’t log anything in 7 days
    result = await db.execute(
        select(HealthDiary.user_id)
        .where(
            HealthDiary.user_id.in_(patient_ids),
            HealthDiary.date >= week_ago
        )
    )
    recent_log_ids = {row[0] for row in result.fetchall()}
    missing_logs = list(set(patient_ids) - recent_log_ids)

    return {
        "total_patients": len(patient_ids),
        "active_patients_last_7_days": active_patients,
        "common_symptoms": common_symptoms,
        "adherence_rate": adherence_rate,
        "missing_logs": missing_logs
    }
