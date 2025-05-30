from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.endpoints.dependencies import get_current_user
from app.schemas.digital_wallet import (
    DigitalCredential,
    CredentialShareRequest,
    CredentialVerificationRequest,
    DigitalWalletResponse,
    CredentialType,
    CredentialStatus
)
from app.crud.digital_wallet import (
    create_digital_credential,
    get_user_credentials,
    share_credential,
    verify_credential,
    get_credential_shares,
    revoke_credential_share
)
from typing import List, Optional
from datetime import datetime

router = APIRouter()

@router.post("/credentials", response_model=DigitalCredential)
async def create_credential(
    credential_type: CredentialType,
    credential_data: dict,
    issuer: str,
    expires_at: Optional[datetime] = None,
    credential_metadata: Optional[dict] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new digital credential."""
    try:
        credential = await create_digital_credential(
            db=db,
            user_id=current_user.id,
            credential_type=credential_type,
            credential_data=credential_data,
            issuer=issuer,
            expires_at=expires_at,
            credential_metadata=credential_metadata
        )
        return credential
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/credentials", response_model=DigitalWalletResponse)
async def list_credentials(
    credential_type: Optional[CredentialType] = None,
    status: Optional[CredentialStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all credentials for the current user."""
    try:
        credentials = await get_user_credentials(
            db=db,
            user_id=current_user.id,
            credential_type=credential_type,
            status=status
        )
        
        # Convert SQLAlchemy models to Pydantic models
        credential_schemas = [
            DigitalCredential(
                id=cred.id,
                user_id=cred.user_id,
                credential_type=cred.credential_type,
                credential_data=cred.credential_data,
                status=cred.status,
                issued_at=cred.issued_at,
                expires_at=cred.expires_at,
                issuer=cred.issuer,
                verification_status=cred.verification_status,
                verification_timestamp=cred.verification_timestamp,
                credential_metadata=cred.credential_metadata
            )
            for cred in credentials
        ]
        
        # Calculate statistics
        total_credentials = len(credential_schemas)
        active_credentials = len([c for c in credential_schemas if c.status == CredentialStatus.ACTIVE])
        expired_credentials = len([c for c in credential_schemas if c.status == CredentialStatus.EXPIRED])
        verification_status = {
            "verified": len([c for c in credential_schemas if c.verification_status]),
            "unverified": len([c for c in credential_schemas if not c.verification_status])
        }
        
        return DigitalWalletResponse(
            credentials=credential_schemas,
            total_credentials=total_credentials,
            active_credentials=active_credentials,
            expired_credentials=expired_credentials,
            verification_status=verification_status
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/credentials/{credential_id}/share", response_model=dict)
async def share_credential_endpoint(
    credential_id: int,
    share_request: CredentialShareRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Share a credential with another user."""
    try:
        share = await share_credential(
            db=db,
            share_request=share_request,
            user_id=current_user.id
        )
        
        # In a real implementation, you would send an email notification here
        # background_tasks.add_task(send_credential_share_notification, share)
        
        return {
            "message": "Credential shared successfully",
            "share_id": share.id
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/credentials/{credential_id}/verify", response_model=dict)
async def verify_credential_endpoint(
    credential_id: int,
    verification_request: CredentialVerificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Verify a credential using the specified method."""
    try:
        verification = await verify_credential(
            db=db,
            verification_request=verification_request,
            user_id=current_user.id
        )
        return {
            "message": "Credential verification completed",
            "verification_id": verification.id,
            "verification_result": verification.verification_result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/credentials/{credential_id}/shares", response_model=List[dict])
async def list_credential_shares(
    credential_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all shares for a specific credential."""
    try:
        shares = await get_credential_shares(
            db=db,
            credential_id=credential_id,
            user_id=current_user.id
        )
        return [
            {
                "id": share.id,
                "recipient_email": share.recipient_email,
                "recipient_name": share.recipient_name,
                "purpose": share.purpose,
                "created_at": share.created_at,
                "expires_at": share.expires_at,
                "is_active": share.is_active
            }
            for share in shares
        ]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/credentials/shares/{share_id}")
async def revoke_share(
    share_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Revoke a credential share."""
    try:
        await revoke_credential_share(
            db=db,
            share_id=share_id,
            user_id=current_user.id
        )
        return {"message": "Share revoked successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 