from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.report_service import generate_health_report
from app.services.auth_service import verify_access_token  
from fastapi.responses import FileResponse
import os

router = APIRouter()

async def get_current_user(token: str = Depends(verify_access_token)):
    """Dependency to validate and return the current authenticated user from the token."""
    return token 


@router.post("/reports/generate", dependencies=[Depends(get_current_user)])
async def generate_report_endpoint(user_id: int, db: AsyncSession = Depends(get_db)):
    """Generate a PDF health report for a user. Requires authentication."""
    report_path = await generate_health_report(user_id)
    if not report_path:
        raise HTTPException(status_code=400, detail="Failed to generate report.")
    return {"message": "Report generated successfully", "report_path": report_path}


@router.get("/reports/download/{report_id}", dependencies=[Depends(get_current_user)])
async def download_report_endpoint(report_id: int):
    """Download a generated PDF report. Requires authentication."""
    report_path = f"reports/user_{report_id}_health_report.pdf"

    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(report_path, filename=f"user_{report_id}_health_report.pdf", media_type='application/pdf')
