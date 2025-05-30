SUBSCRIPTION_TIERS = {
    "freemium": {
        "features": ["health_diary", "basic_symptom_tracking", "medication_reminders", "limited_ai_health_tips"],
        "cost": {"AUD": 0, "NZD": 0, "USD": 0, "GBP": 0, "CAD": 0},
    },
    "premium_family": {
        "features": ["unlimited_profiles", "advanced_ai_insights", "custom_health_reports", "priority_support"],
        "cost": {"AUD": 10, "NZD": 12, "USD": 8, "GBP": 6, "CAD": 10},
    },
    "healthcare_provider": {
        "features": ["practitioner_dashboard", "telehealth", "secure_messaging", "ehr_integration"],
        "cost": {"AUD": 200, "NZD": 220, "USD": 150, "GBP": 120, "CAD": 200},
    },
    "enterprise": {
        "features": ["full_ehr_integration", "population_health_analytics", "custom_branding", "priority_support", "data_analytics"],
        "cost": {"AUD": 10000, "NZD": 11000, "USD": 8000, "GBP": 6500, "CAD": 10000},
    },
}
