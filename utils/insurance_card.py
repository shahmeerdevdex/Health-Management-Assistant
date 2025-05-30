from app.db.models.insurance import InsurancePlan

def generate_wallet_card_json(insurance: InsurancePlan) -> dict:
    return {
        "type": "health_insurance",
        "provider": insurance.provider_name,
        "policy_number": insurance.policy_number,
        "valid_from": str(insurance.coverage_start),
        "valid_until": str(insurance.coverage_end),
        "is_verified": insurance.is_verified,
        "verification_status": insurance.verification_status,
    }
