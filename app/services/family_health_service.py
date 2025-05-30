from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from app.db.models.family import FamilyLink, FamilyHealthSummary
from app.db.models.user import User
from app.db.models.health_diary import HealthDiary
from app.db.models.medication import Medication
from app.db.models.appointments import Appointment,AppointmentStatus


class FamilyHealthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _serialize_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        """Convert datetime to ISO format string."""
        if dt is None:
            return None
        return dt.isoformat()

    async def generate_family_health_summary(self, family_link_id: int) -> FamilyHealthSummary:
        """Generate a comprehensive health summary for a family unit."""
        # Get family link
        family_link = await self._get_family_link(family_link_id)
        if not family_link:
            raise ValueError(f"Family link {family_link_id} not found")

        # Get all family members
        family_members = await self._get_family_members(family_link)
        
        # Collect health data
        health_data = await self._collect_family_health_data(family_members)
        
        # Create or update summary
        summary = await self._create_or_update_summary(family_link_id, health_data)
        
        return summary

    async def _get_family_link(self, family_link_id: int) -> Optional[FamilyLink]:
        """Get family link by ID."""
        result = await self.db.execute(
            select(FamilyLink).where(FamilyLink.id == family_link_id)
        )
        return result.scalar_one_or_none()

    async def _get_family_members(self, family_link: FamilyLink) -> List[User]:
        """Get all members of a family unit."""
        # Get the primary user and family member
        primary_user = await self.db.execute(
            select(User).where(User.id == family_link.user_id)
        )
        primary_user = primary_user.scalar_one_or_none()
        
        family_member = await self.db.execute(
            select(User).where(User.id == family_link.family_member_id)
        )
        family_member = family_member.scalar_one_or_none()
        
        members = []
        if primary_user:
            members.append(primary_user)
        if family_member:
            members.append(family_member)
        
        # Get additional family members if any
        additional_links = await self.db.execute(
            select(FamilyLink).where(
                (FamilyLink.user_id == family_link.user_id) |
                (FamilyLink.family_member_id == family_link.user_id)
            )
        )
        additional_links = additional_links.scalars().all()
        
        for link in additional_links:
            # Get user and family member for each link
            user = await self.db.execute(
                select(User).where(User.id == link.user_id)
            )
            user = user.scalar_one_or_none()
            
            member = await self.db.execute(
                select(User).where(User.id == link.family_member_id)
            )
            member = member.scalar_one_or_none()
            
            if user and user not in members:
                members.append(user)
            if member and member not in members:
                members.append(member)
        
        return members

    async def _collect_family_health_data(self, family_members: List[User]) -> Dict[str, Any]:
        """Collect health data from all family members."""
        health_data = {
            "medications": [],
            "upcoming_appointments": [],
            "recent_health_events": [],
            "overall_health_status": "good"  # Default status
        }

        for member in family_members:
            # Get recent health diary entries
            recent_entries = await self._get_recent_health_entries(member.id)
            if recent_entries:
                health_data["recent_health_events"].extend(recent_entries)

            # Get medications
            medications = await self._get_active_medications(member.id)
            if medications:
                health_data["medications"].extend(medications)

            # Get appointments
            appointments = await self._get_upcoming_appointments(member.id)
            if appointments:
                health_data["upcoming_appointments"].extend(appointments)
        
        return health_data

    async def _get_recent_health_entries(self, user_id: int) -> List[Dict[str, Any]]:
        """Get recent health diary entries."""
        recent_date = datetime.utcnow() - timedelta(days=30)
        result = await self.db.execute(
            select(HealthDiary)
            .where(HealthDiary.user_id == user_id)
            .where(HealthDiary.date >= recent_date)
            .order_by(HealthDiary.date.desc())
        )
        entries = result.scalars().all()
        return [{
            "date": self._serialize_datetime(e.date),
            "health_metrics": e.health_metrics,
            "symptoms": e.symptoms,
            "mood": e.mood,
            "notes": e.notes
        } for e in entries]

    async def _get_active_medications(self, user_id: int) -> List[Dict[str, Any]]:
        """Get active medications."""
        result = await self.db.execute(
            select(Medication)
            .where(Medication.user_id == user_id)
            .where(
                (Medication.end_date == None) |
                (Medication.end_date >= datetime.utcnow())
            )
        )
        medications = result.scalars().all()
        return [{
            "name": m.name,
            "dosage": m.dosage,
            "frequency": m.frequency,
            "start_date": self._serialize_datetime(m.start_date),
            "end_date": self._serialize_datetime(m.end_date)
        } for m in medications]

    async def _get_upcoming_appointments(self, user_id: int) -> List[Dict[str, Any]]:
        """Get upcoming appointments."""
        result = await self.db.execute(
            select(Appointment)
            .where(Appointment.user_id == user_id)
            .where(Appointment.date >= datetime.utcnow())
            .where(Appointment.status.in_([
                AppointmentStatus.SCHEDULED,
                AppointmentStatus.CONFIRMED
            ]))
            .order_by(Appointment.date)
        )
        appointments = result.scalars().all()
        return [{
            "date": self._serialize_datetime(a.date),
            "type": a.appointment_type,
            "provider_type": a.provider_type,
            "status": a.status,
            "duration": a.duration,
            "location": a.location
        } for a in appointments]

    def _calculate_overall_status(self, health_data: Dict[str, Any]) -> str:
        """Calculate overall family health status."""
        risk_count = len(health_data["risk_factors"])
        if risk_count > 3:
            return "poor"
        elif risk_count > 1:
            return "fair"
        return "good"

    async def _create_or_update_summary(
        self, family_link_id: int, health_data: Dict[str, Any]
    ) -> FamilyHealthSummary:
        """Create or update family health summary."""
        # Check for existing summary
        result = await self.db.execute(
            select(FamilyHealthSummary)
            .where(FamilyHealthSummary.family_id == family_link_id)
            .order_by(FamilyHealthSummary.generated_at.desc())
        )
        existing_summary = result.scalar_one_or_none()

        if existing_summary:
            # Update existing summary
            for key, value in health_data.items():
                setattr(existing_summary, key, value)
            existing_summary.last_updated = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(existing_summary)
            return existing_summary
        else:
            # Create new summary
            new_summary = FamilyHealthSummary(
                family_id=family_link_id,
                generated_at=datetime.utcnow(),
                last_updated=datetime.utcnow(),
                **health_data
            )
            self.db.add(new_summary)
            await self.db.commit()
            await self.db.refresh(new_summary)
            return new_summary 