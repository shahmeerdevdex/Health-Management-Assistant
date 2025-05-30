from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import datetime
import qrcode
import io
import base64
from typing import Optional, Dict, Any

from app.db.models.emergency_health_ids import EmergencyHealthID
from app.schemas.emergency_health_ids import EmergencyHealthIDCreate, EmergencyHealthIDResponse, EmergencyHealthIDWallet
from app.services.digital_wallet_service import DigitalWalletService
from app.db.models.user import User

class EmergencyHealthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.digital_wallet = DigitalWalletService()

    async def create_or_update_health_id(
        self,
        user_id: int,
        health_data: EmergencyHealthIDCreate
    ) -> EmergencyHealthIDResponse:
        """Create or update emergency health ID with QR code generation."""
        result = await self.db.execute(
            select(EmergencyHealthID).filter(EmergencyHealthID.user_id == user_id)
        )
        existing_health_id = result.scalars().first()

        if existing_health_id:
            # Update existing record
            for key, value in health_data.dict().items():
                setattr(existing_health_id, key, value)
            
            if health_data.qr_code_enabled:
                existing_health_id.qr_code = await self._generate_qr_code(existing_health_id)
            
            existing_health_id.updated_at = datetime.utcnow()
        else:
            # Create new record
            new_health_id = EmergencyHealthID(
                user_id=user_id,
                **health_data.dict()
            )
            if health_data.qr_code_enabled:
                new_health_id.qr_code = await self._generate_qr_code(new_health_id)
            
            self.db.add(new_health_id)
            existing_health_id = new_health_id

        await self.db.commit()
        await self.db.refresh(existing_health_id)
        return EmergencyHealthIDResponse.from_orm(existing_health_id)

    async def get_health_id(self, user_id: int) -> Optional[EmergencyHealthIDResponse]:
        """Get emergency health ID with access tracking."""
        result = await self.db.execute(
            select(EmergencyHealthID).filter(EmergencyHealthID.user_id == user_id)
        )
        health_id = result.scalars().first()
        
        if health_id:
            # Update access tracking
            health_id.last_accessed = datetime.utcnow()
            health_id.access_count += 1
            await self.db.commit()
            await self.db.refresh(health_id)
            
            return EmergencyHealthIDResponse.from_orm(health_id)
        return None

    async def get_wallet_format(self, user_id: int) -> Optional[EmergencyHealthIDWallet]:
        """Get emergency health ID in digital wallet format."""
        result = await self.db.execute(
            select(EmergencyHealthID)
            .options(selectinload(EmergencyHealthID.user))
            .filter(EmergencyHealthID.user_id == user_id)
        )
        health_id = result.scalars().first()
        
        if not health_id:
            return None

        # Update access tracking
        health_id.last_accessed = datetime.utcnow()
        health_id.access_count += 1
        await self.db.commit()
        await self.db.refresh(health_id)

        wallet_data = {
            "type": "emergencyHealthID",
            "formatVersion": 1,
            "passTypeIdentifier": "pass.com.health.emergency.id",
            "teamIdentifier": "YOUR_TEAM_ID",
            "organizationName": "Health Management Assistant",
            "description": "Emergency Health ID",
            "logoText": "Emergency Health ID",
            "generic": {
                "primaryFields": [
                    {
                        "key": "name",
                        "label": "NAME",
                        "value": health_id.user.full_name
                    },
                    {
                        "key": "bloodType",
                        "label": "BLOOD TYPE",
                        "value": health_id.blood_type.value if health_id.blood_type else "Unknown"
                    }
                ],
                "secondaryFields": [
                    {
                        "key": "emergencyContact",
                        "label": "EMERGENCY CONTACT",
                        "value": f"{health_id.emergency_contact_name} ({health_id.emergency_contact_phone})"
                    }
                ],
                "auxiliaryFields": [
                    {
                        "key": "allergies",
                        "label": "ALLERGIES",
                        "value": health_id.allergies or "None"
                    },
                    {
                        "key": "conditions",
                        "label": "CRITICAL CONDITIONS",
                        "value": health_id.critical_conditions or "None"
                    }
                ]
            }
        }

        return EmergencyHealthIDWallet(
            **EmergencyHealthIDResponse.from_orm(health_id).dict(),
            wallet_format=wallet_data
        )

    async def _generate_qr_code(self, health_id: EmergencyHealthID) -> str:
        """Generate QR code for emergency health ID."""
        # Create QR code data
        qr_data = {
            "id": health_id.id,
            "user_id": health_id.user_id,
            "blood_type": health_id.blood_type.value if health_id.blood_type else None,
            "allergies": health_id.allergies,
            "critical_conditions": health_id.critical_conditions,
            "emergency_contact": {
                "name": health_id.emergency_contact_name,
                "phone": health_id.emergency_contact_phone
            }
        }

        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(str(qr_data))
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()

    async def toggle_lock_screen(self, user_id: int, enabled: bool) -> bool:
        """Toggle lock screen integration for emergency health ID."""
        result = await self.db.execute(
            select(EmergencyHealthID).filter(EmergencyHealthID.user_id == user_id)
        )
        health_id = result.scalars().first()
        
        if health_id:
            health_id.lock_screen_enabled = enabled
            await self.db.commit()
            return True
        return False 