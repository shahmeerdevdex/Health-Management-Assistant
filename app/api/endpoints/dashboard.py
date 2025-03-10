from fastapi import APIRouter, Depends, HTTPException
from app.core.ai_services import detect_health_patterns
from app.services.auth_service import verify_access_token

router = APIRouter()


@router.get("/dashboard/{user_id}")
async def get_dashboard_endpoint(
    user_id: int,
    token_data: dict = Depends(verify_access_token),
):
    """
    Fetch dashboard data for a user.

    - **Requires Authentication** via access token.
    - **Parameters:**
        - `user_id`: The ID of the user whose dashboard data is being requested.
        - `token_data`: The decoded access token to ensure authentication.
    - **Returns:** A JSON object with dashboard data.
    """
    if token_data["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return {"message": f"Dashboard data for user {user_id}"}


@router.post("/dashboard/ai-insights")
async def get_ai_insights_endpoint(
    user_id: int,
    token_data: dict = Depends(verify_access_token),
):
    """
    Fetch AI-driven insights for the user's health patterns.

    - **Requires Authentication** via access token.
    - **Parameters:**
        - `user_id`: The ID of the user for whom AI insights are requested.
        - `token_data`: The decoded access token to ensure authentication.
    - **Returns:** AI-driven health insights based on the user's health data.
    """
    if token_data["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return await detect_health_patterns(user_id)
