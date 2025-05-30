from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from app.db.models.digital_wallet import DigitalCredential, CredentialShare, CredentialVerification
from app.schemas.digital_wallet import (
    DigitalCredential as DigitalCredentialSchema,
    CredentialShareRequest,
    CredentialVerificationRequest,
    CredentialStatus,
    CredentialType
)

async def create_digital_credential(
    db: AsyncSession,
    user_id: int,
    credential_type: CredentialType,
    credential_data: Dict[str, Any],
    issuer: str,
    expires_at: Optional[datetime] = None,
    credential_metadata: Optional[Dict[str, Any]] = None
) -> DigitalCredential:
    """Create a new digital credential."""
    # Get current time in UTC
    current_time = datetime.now(timezone.utc)
    
    # Convert timezone-aware datetimes to naive datetimes
    if expires_at:
        if expires_at.tzinfo is not None:
            expires_at = expires_at.replace(tzinfo=None)
    
    credential = DigitalCredential(
        user_id=user_id,
        credential_type=credential_type,
        credential_data=credential_data,
        issuer=issuer,
        expires_at=expires_at,
        credential_metadata=credential_metadata,
        issued_at=current_time.replace(tzinfo=None),  # Convert to naive datetime
        status=CredentialStatus.PENDING
    )
    db.add(credential)
    await db.commit()
    await db.refresh(credential)
    return credential

async def get_user_credentials(
    db: AsyncSession,
    user_id: int,
    credential_type: Optional[CredentialType] = None,
    status: Optional[CredentialStatus] = None
) -> List[DigitalCredential]:
    """Get all credentials for a user with optional filtering."""
    query = select(DigitalCredential).filter(DigitalCredential.user_id == user_id)
    
    if credential_type:
        query = query.filter(DigitalCredential.credential_type == credential_type)
    if status:
        query = query.filter(DigitalCredential.status == status)
    
    result = await db.execute(query)
    return result.scalars().all()

async def share_credential(
    db: AsyncSession,
    share_request: CredentialShareRequest,
    user_id: int
) -> CredentialShare:
    """Share a credential with another user."""
    # Verify credential ownership
    credential = await db.execute(
        select(DigitalCredential).filter(
            and_(
                DigitalCredential.id == share_request.credential_id,
                DigitalCredential.user_id == user_id
            )
        )
    )
    credential = credential.scalar_one_or_none()
    if not credential:
        raise ValueError("Credential not found or unauthorized")

    # Calculate expiration
    expires_at = None
    if share_request.access_duration:
        expires_at = datetime.utcnow() + timedelta(hours=share_request.access_duration)

    share = CredentialShare(
        credential_id=share_request.credential_id,
        recipient_email=share_request.recipient_email,
        recipient_name=share_request.recipient_name,
        access_duration=share_request.access_duration,
        purpose=share_request.purpose,
        scope=share_request.scope,
        expires_at=expires_at
    )
    db.add(share)
    await db.commit()
    await db.refresh(share)
    return share

async def verify_credential(
    db: AsyncSession,
    verification_request: CredentialVerificationRequest,
    user_id: int
) -> CredentialVerification:
    """Verify a credential using the specified method."""
    # Verify credential ownership
    credential = await db.execute(
        select(DigitalCredential).filter(
            and_(
                DigitalCredential.id == verification_request.credential_id,
                DigitalCredential.user_id == user_id
            )
        )
    )
    credential = credential.scalar_one_or_none()
    if not credential:
        raise ValueError("Credential not found or unauthorized")

    # Perform verification based on method
    verification_result = await _perform_verification(
        verification_request.verification_method,
        verification_request.verification_data
    )

    verification = CredentialVerification(
        credential_id=verification_request.credential_id,
        verification_method=verification_request.verification_method,
        verification_data=verification_request.verification_data,
        verification_result=verification_result
    )
    db.add(verification)

    # Update credential verification status
    credential.verification_status = verification_result
    credential.verification_timestamp = datetime.utcnow()

    await db.commit()
    await db.refresh(verification)
    return verification

async def _perform_verification(
    method: str,
    data: Dict[str, Any]
) -> bool:
    """Perform credential verification based on the specified method."""
    # This is a placeholder for actual verification logic
    # In a real implementation, this would integrate with various verification services
    if method == "medicare_verification":
        # Implement Medicare verification logic
        return True
    elif method == "smart_health_card_verification":
        # Implement SMART Health Card verification logic
        return True
    elif method == "manual_verification":
        # Implement manual verification logic
        return True
    else:
        raise ValueError(f"Unsupported verification method: {method}")

async def get_credential_shares(
    db: AsyncSession,
    credential_id: int,
    user_id: int
) -> List[CredentialShare]:
    """Get all shares for a specific credential."""
    # Verify credential ownership
    credential = await db.execute(
        select(DigitalCredential).filter(
            and_(
                DigitalCredential.id == credential_id,
                DigitalCredential.user_id == user_id
            )
        )
    )
    credential = credential.scalar_one_or_none()
    if not credential:
        raise ValueError("Credential not found or unauthorized")

    result = await db.execute(
        select(CredentialShare).filter(CredentialShare.credential_id == credential_id)
    )
    return result.scalars().all()

async def revoke_credential_share(
    db: AsyncSession,
    share_id: int,
    user_id: int
) -> None:
    """Revoke a credential share."""
    # Verify credential ownership through the share
    share = await db.execute(
        select(CredentialShare).join(DigitalCredential).filter(
            and_(
                CredentialShare.id == share_id,
                DigitalCredential.user_id == user_id
            )
        )
    )
    share = share.scalar_one_or_none()
    if not share:
        raise ValueError("Share not found or unauthorized")

    share.is_active = False
    await db.commit() 