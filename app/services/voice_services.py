import os
import io
from fastapi import HTTPException
import openai
from elevenlabs.client import ElevenLabs  
from app.core.config import settings

# Load API Keys from environment variables
OPENAI_API_KEY = settings.OPENAI_API_KEY
ELEVENLABS_API_KEY = settings.ELEVENLABS_API_KEY

# Validate API Keys
if not OPENAI_API_KEY:
    raise RuntimeError("Missing OpenAI API key. Set OPENAI_API_KEY in environment variables.")

if not ELEVENLABS_API_KEY:
    raise RuntimeError("Missing ElevenLabs API key. Set ELEVENLABS_API_KEY in environment variables.")


async def transcribe_audio(audio_file: bytes):
    """Convert speech to text using OpenAI Whisper."""
    try:
        response = openai.Audio.transcribe(
            model="whisper-1",
            file=io.BytesIO(audio_file)
        )
        return response["text"]
    except openai.error.OpenAIError as e:
        raise HTTPException(status_code=500, detail=f"OpenAI Whisper Error: {str(e)}")


async def generate_speech(text: str, voice_name: str = "Rachel") -> bytes:
    """Convert text to speech using ElevenLabs and return as bytes."""
    try:
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

        # Get available voices
        voices = client.voices.get_all()
        selected_voice = next((v for v in voices.voices if v.name.lower() == voice_name.lower()), None)

        if not selected_voice:
            selected_voice = voices.voices[0] if voices.voices else None
            if not selected_voice:
                raise HTTPException(status_code=404, detail="No voices available.")

        # Generate the audio stream (generator)
        audio_stream = client.text_to_speech.convert(
            text=text,
            voice_id=selected_voice.voice_id,
            model_id="eleven_monolingual_v1",
           output_format="mp3_44100_128"
        )

        # Convert generator to full bytes
        audio_bytes = b"".join(audio_stream)
        return audio_bytes

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ElevenLabs TTS Error: {str(e)}")
