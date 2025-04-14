from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.report_service import generate_health_report
from app.api.endpoints.dependencies import get_current_user  
from fastapi.responses import FileResponse
import os

router = APIRouter()

@router.post("/generate")
async def generate_report_endpoint(
    db_user=Depends(get_current_user),  
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a PDF health report for the authenticated user.

    - Requires authentication via access token.
    - Returns the path to the generated report.
    """
    report_path = await generate_health_report(db_user.id)  

    if not report_path:
        raise HTTPException(status_code=400, detail="Failed to generate report.")

    return {"message": "Report generated successfully", "report_path": report_path}

@router.get("/download/{report_id}")
async def download_report_endpoint(
    db_user=Depends(get_current_user)  
):
    """
    Download a generated PDF report.

    - Requires authentication via access token.
    - Returns the requested report as a downloadable file.
    """
    report_path = f"reports/user_{db_user.id}_health_report.pdf"  

    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(report_path, filename=f"user_{db_user.id}_health_report.pdf", media_type='application/pdf')
