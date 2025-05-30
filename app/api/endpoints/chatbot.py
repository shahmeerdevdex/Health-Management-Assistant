from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.ai_chatbot import generate_health_advice
from app.api.endpoints.dependencies import get_db,get_current_user
from app.schemas.chatbot import ChatbotRequest, ChatbotResponse

router = APIRouter()

@router.post("/chat", response_model=ChatbotResponse)
async def chat_with_ai(request: ChatbotRequest, db: AsyncSession = Depends(get_db),db_user=Depends(get_current_user)):
    """AI Chatbot Endpoint for Health Advice."""
    try:
        ai_response = await generate_health_advice(request.user_id, request.message, db)
        return {"response": ai_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
