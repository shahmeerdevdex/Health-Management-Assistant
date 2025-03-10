import logging

logger = logging.getLogger("telehealth_service")

async def start_telehealth_session(user_id: int, practitioner_id: int):
    """Start a telehealth session between a user and a practitioner."""
    session_id = f"session_{user_id}_{practitioner_id}"
    logger.info(f"Telehealth session started: {session_id}")
    return await {"session_id": session_id, "message": "Telehealth session started successfully."}
