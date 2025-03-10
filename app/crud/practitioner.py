from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from app.db.models.practitioners import Practitioner  
from app.schemas.practitioner import PractitionerCreate, PractitionerResponse

async def create_practitioner(db: AsyncSession, practitioner: PractitionerCreate):
    """Create a new practitioner."""
    db_practitioner = Practitioner(
        name=practitioner.name,
        specialty=practitioner.specialty,
        contact_info=practitioner.contact_info,
    )
    db.add(db_practitioner)
    await db.commit()
    await db.refresh(db_practitioner)
    return db_practitioner

from app.schemas.practitioner import PractitionerResponse  

async def get_practitioners(db: AsyncSession):
    result = await db.execute(select(Practitioner))
    practitioners = result.scalars().all()
    
    # Convert ORM objects to Pydantic models
    return [PractitionerResponse.from_orm(p) for p in practitioners]

async def get_practitioner_by_id(db: AsyncSession, practitioner_id: int):
    """Get a single practitioner by ID."""
    result = await db.execute(select(Practitioner).filter(Practitioner.id == practitioner_id))
    return result.scalars().first()

async def update_practitioner(db: AsyncSession, practitioner_id: int, practitioner_update: PractitionerCreate):
    """Update a practitioner's details."""
    result = await db.execute(select(Practitioner).filter(Practitioner.id == practitioner_id))
    db_practitioner = result.scalars().first()
    
    if db_practitioner:
        for key, value in practitioner_update.model_dump(exclude_unset=True).items():
            setattr(db_practitioner, key, value)
        await db.commit()
        await db.refresh(db_practitioner)
    
    return db_practitioner

async def delete_practitioner(db: AsyncSession, practitioner_id: int):
    """Delete a practitioner by ID."""
    result = await db.execute(select(Practitioner).filter(Practitioner.id == practitioner_id))
    db_practitioner = result.scalars().first()

    if db_practitioner:
        await db.delete(db_practitioner)
        await db.commit()
    
    return db_practitioner
