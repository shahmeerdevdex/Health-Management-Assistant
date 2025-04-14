from fastapi import APIRouter, UploadFile, File, Depends, Response, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.voice_services import transcribe_audio, generate_speech
from app.api.endpoints.dependencies import get_db, get_current_user

router = APIRouter()

@router.post("/voice/log-entry")
async def log_voice_entry(
    audio: UploadFile = File(...), 
    db: AsyncSession = Depends(get_db), 
    user=Depends(get_current_user)
):
    """
    Transcribe a voice command using Whisper and return the text.
    """
    audio_bytes = await audio.read()
    text_command = await transcribe_audio(audio_bytes)

    return {"message": "Voice entry logged", "recognized_text": text_command}


@router.get("/voice/read-text")
async def read_text(
    text: str,
    voice_name: str = "Rachel",  
    db:AsyncSession = Depends(get_db), 
    user=Depends(get_current_user)
):
    """Generate speech from text using ElevenLabs."""
    audio_content = await generate_speech(text, voice_name)
    return Response(content=audio_content, media_type="audio/mpeg")
