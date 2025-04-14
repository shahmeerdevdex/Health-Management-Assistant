from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.diagnostics import HomeDiagnosticsRequest, HomeDiagnosticsResponse
from app.services.diagnostics_service import process_home_diagnostics
from app.api.endpoints.dependencies import get_db,get_current_user


router = APIRouter()

@router.post("/home-tests", response_model=HomeDiagnosticsResponse)
async def home_diagnostics(
    request: HomeDiagnosticsRequest,
    db: Session = Depends(get_db),
    db_user = Depends(get_current_user)
):
    """
    Processes home diagnostic test results and provides insights.
    """
    try:
        diagnostics_data = await process_home_diagnostics(request, db)
        return diagnostics_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
