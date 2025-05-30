from pydantic import BaseModel

class ChatbotRequest(BaseModel):
    user_id: int
    message: str

class ChatbotResponse(BaseModel):
    response: str
