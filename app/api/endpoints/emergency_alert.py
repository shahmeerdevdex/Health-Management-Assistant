from fastapi import APIRouter

router = APIRouter()

@router.post("/emergency/alert")
async def send_emergency_alert(user_id: int, message: str):
    return await {"message": f"Emergency alert sent for user {user_id}: {message}"}
