import requests
from app.core.config import settings

def verify_practitioner_with_ahpra(registration_number: str) -> dict:
    """Calls the AHPRA PIE API to verify a practitioner's registration."""
    headers = {
        "Authorization": f"Bearer {settings.AHPRA_PIE_API_KEY}"
    }
    response = requests.get(
        f"https://pie.ahpra.gov.au/api/lookup/{registration_number}",
        headers=headers,
        timeout=10
    )

    if response.status_code != 200:
        raise ValueError("Practitioner not found or AHPRA service error")

    data = response.json()
    return {
        "name": data.get("name"),
        "registration_status": data.get("registration_status"),
        "last_updated": data.get("last_updated"),
        "reference": "https://www.ahpra.gov.au/"
    }
