from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.notification import NotificationCreate, NotificationResponse
from app.crud.notification import create_notification
from app.services.auth_service import verify_access_token  

router = APIRouter()

@router.post("/notifications/send", response_model=NotificationResponse)
async def send_notification_endpoint(
    notification: NotificationCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_access_token)  
):
    """
     **Send a Notification**
    
    This endpoint allows authenticated users to send notifications.

    ###  Requirements:
    - **Authentication:** Must provide a valid access token.
    - **Database Storage:** The notification is saved in the database.
    
    ###  Request Body:
    - `user_id` (int): ID of the recipient user.
    - `message` (str): The notification message.

    ###  Response:
    - Returns the created notification object with `id`, `user_id`, `message`, and `sent_at`.

    ###  Error Handling:
    - **400 Bad Request:** If the notification fails to save.
    """
    new_notification = await create_notification(db, notification)

    if not new_notification:
        raise HTTPException(status_code=400, detail="Failed to send notification.")

    return new_notification  # Return structured response
