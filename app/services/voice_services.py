import os
import io
from fastapi import HTTPException
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings
from app.core.config import settings

# Load API Keys from environment variables
OPENAI_API_KEY = settings.OPENAI_API_KEY
ELEVENLABS_API_KEY = settings.ELEVENLABS_API_KEY

# Validate API Keys
if not OPENAI_API_KEY:
    raise RuntimeError("Missing OpenAI API key. Set OPENAI_API_KEY in environment variables.")

if not ELEVENLABS_API_KEY:
    raise RuntimeError("Missing ElevenLabs API key. Set ELEVENLABS_API_KEY in environment variables.")

# Initialize clients
openai_client = OpenAI(api_key=OPENAI_API_KEY)
elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Voice settings for different accessibility needs
VOICE_SETTINGS = {
    "slow": VoiceSettings(stability=0.5, similarity_boost=0.75, style=0.0, use_speaker_boost=True),
    "normal": VoiceSettings(stability=0.5, similarity_boost=0.5, style=0.0, use_speaker_boost=True),
    "fast": VoiceSettings(stability=0.5, similarity_boost=0.5, style=0.0, use_speaker_boost=True)
}

# Language-specific voice mappings
LANGUAGE_VOICES = {
    "en": {
        "default": "Rachel",
        "options": ["Rachel", "Domi", "Bella", "Antoni", "Elli", "Josh", "Arnold", "Adam", "Sam"]
    },
    "es": {
        "default": "Antoni",
        "options": ["Antoni", "Bella", "Elli"]
    },
    "fr": {
        "default": "Bella",
        "options": ["Bella", "Antoni", "Elli"]
    },
    "de": {
        "default": "Bella",
        "options": ["Bella", "Antoni", "Elli"]
    },
    "it": {
        "default": "Bella",
        "options": ["Bella", "Antoni", "Elli"]
    },
    "pt": {
        "default": "Antoni",
        "options": ["Antoni", "Bella", "Elli"]
    },
    "pl": {
        "default": "Bella",
        "options": ["Bella", "Antoni", "Elli"]
    },
    "tr": {
        "default": "Bella",
        "options": ["Bella", "Antoni", "Elli"]
    }
}

async def transcribe_audio(audio_file: bytes):
    """Convert speech to text using OpenAI Whisper."""
    try:
        response = openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=io.BytesIO(audio_file)
        )
        return response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI Whisper Error: {str(e)}")

async def get_available_voices(language_code: str = None) -> list:
    """Get available voices from ElevenLabs, optionally filtered by language."""
    try:
        voices = elevenlabs_client.voices.get_all()
        if language_code and language_code in LANGUAGE_VOICES:
            return [v for v in voices.voices if v.name in LANGUAGE_VOICES[language_code]["options"]]
        return voices.voices
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching voices: {str(e)}")

async def generate_speech(
    text: str,
    voice_name: str = "Rachel",
    speed: float = 1.0,
    stability: float = 0.5,
    similarity_boost: float = 0.5,
    style: float = 0.0,
    use_speaker_boost: bool = True
) -> bytes:
    """Convert text to speech using ElevenLabs with enhanced settings."""
    try:
        # Get available voices
        voices = await get_available_voices()
        selected_voice = next((v for v in voices if v.name.lower() == voice_name.lower()), None)

        if not selected_voice:
            # Fallback to default voice if specified voice not found
            selected_voice = next((v for v in voices if v.name.lower() == "rachel"), None)
            if not selected_voice:
                raise HTTPException(status_code=404, detail="No suitable voice found.")

        # Create voice settings
        voice_settings = VoiceSettings(
            stability=stability,
            similarity_boost=similarity_boost,
            style=style,
            use_speaker_boost=use_speaker_boost
        )

        # Generate the audio stream
        audio_stream = elevenlabs_client.text_to_speech.convert(
            text=text,
            voice_id=selected_voice.voice_id,
            model_id="eleven_monolingual_v1",
            voice_settings=voice_settings,
            output_format="mp3_44100_128"
        )

        # Convert generator to full bytes
        audio_bytes = b"".join(audio_stream)
        return audio_bytes

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ElevenLabs TTS Error: {str(e)}")

async def generate_speech_with_accessibility(
    text: str,
    language_code: str = "en",
    voice_name: str = None,
    speed: float = 1.0,
    high_contrast: bool = False
) -> bytes:
    """Generate speech with accessibility settings."""
    try:
        # Get appropriate voice for the language
        if not voice_name:
            voice_name = LANGUAGE_VOICES.get(language_code, {}).get("default", "Rachel")

        # Adjust settings based on accessibility preferences
        stability = 0.7 if high_contrast else 0.5  # Higher stability for clearer speech
        similarity_boost = 0.75 if high_contrast else 0.5  # Higher similarity for more consistent voice

        # Adjust speed
        if speed < 0.8:
            # Slower speech with higher stability
            stability = 0.8
            similarity_boost = 0.8
        elif speed > 1.2:
            # Faster speech with slightly lower stability
            stability = 0.4
            similarity_boost = 0.4

        return await generate_speech(
            text=text,
            voice_name=voice_name,
            speed=speed,
            stability=stability,
            similarity_boost=similarity_boost
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Accessibility TTS Error: {str(e)}")
