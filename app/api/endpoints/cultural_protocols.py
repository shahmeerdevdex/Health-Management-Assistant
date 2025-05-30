from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from app.services.cultural_protocols_service import CulturalProtocolsService
from app.schemas.indigenous_health import IndigenousCommunity
from app.api.endpoints.dependencies import get_db, get_current_user
from app.schemas.user import User

router = APIRouter()

@router.get("/ceremonial/{community}/{ceremony_type}")
async def get_ceremonial_protocols(
    community: IndigenousCommunity,
    ceremony_type: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get ceremonial protocols for a specific community and ceremony type.
    """
    try:
        service = CulturalProtocolsService(db)
        protocols = await service.get_ceremonial_protocols(community, ceremony_type)
        return protocols
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/consultation/{community}")
async def get_cultural_consultation_guidelines(
    community: IndigenousCommunity,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get cultural consultation guidelines for a specific community.
    """
    try:
        service = CulturalProtocolsService(db)
        guidelines = await service.get_cultural_consultation_guidelines(community)
        return guidelines
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-protection/{community}")
async def get_traditional_knowledge_protection(
    community: IndigenousCommunity,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get traditional knowledge protection guidelines for a specific community.
    """
    try:
        service = CulturalProtocolsService(db)
        protection = await service.get_traditional_knowledge_protection(community)
        return protection
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/community-protocols/{community}")
async def get_community_specific_protocols(
    community: IndigenousCommunity,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get community-specific protocols and guidelines.
    """
    try:
        service = CulturalProtocolsService(db)
        protocols = await service.get_community_specific_protocols(community)
        return protocols
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/safety-guidelines/{community}")
async def get_cultural_safety_guidelines(
    community: IndigenousCommunity,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get cultural safety guidelines for health care providers.
    """
    try:
        service = CulturalProtocolsService(db)
        guidelines = await service.get_cultural_safety_guidelines(community)
        return guidelines
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 