from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db import models
from app.schemas import report
from datetime import datetime

async def create_report(db: AsyncSession, report_data: report.ReportCreate):
    """Creates a new report asynchronously."""
    db_report = models.Report(**report_data.dict(), created_at=datetime.utcnow())
    db.add(db_report)
    await db.commit()  
    await db.refresh(db_report)  
    return db_report

async def get_reports_by_user(db: AsyncSession, user_id: int):
    """Fetch reports by user asynchronously."""
    result = await db.execute(select(models.Report).filter(models.Report.user_id == user_id))
    return result.scalars().all()  

async def update_report(db: AsyncSession, report_id: int, report_update: report.ReportUpdate):
    """Updates a report asynchronously."""
    result = await db.execute(select(models.Report).filter(models.Report.id == report_id))
    db_report = result.scalars().first()
    
    if db_report:
        for key, value in report_update.dict(exclude_unset=True).items():
            setattr(db_report, key, value)
        await db.commit()  
        await db.refresh(db_report)  
    return db_report

async def delete_report(db: AsyncSession, report_id: int):
    """Deletes a report asynchronously."""
    result = await db.execute(select(models.Report).filter(models.Report.id == report_id))
    db_report = result.scalars().first()
    
    if db_report:
        await db.delete(db_report) 
        await db.commit() 
    return db_report
