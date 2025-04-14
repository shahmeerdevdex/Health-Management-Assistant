def parse_voice_command(command: str):
    """Detect action from voice command"""
    command = command.lower()

    if "log" in command and "symptom" in command:
        return "log_symptom"
    elif "take" in command and "medication" in command:
        return "log_medication"
    elif "appointment" in command and "schedule" in command:
        return "schedule_appointment"
    else:
        return "unknown_command"
