from sqlalchemy.orm import Session
from app.schemas.wearables import WearableDataRequest, WearableDataResponse

async def process_wearable_data(request: WearableDataRequest, db: Session) -> WearableDataResponse:
    """
    Processes wearable device data and generates health insights.
    """
    insights = []
    
    # Analyze heart rate data
    if request.heart_rate:
        avg_hr = sum(request.heart_rate) / len(request.heart_rate)
        if avg_hr > 100:
            insights.append("Your average heart rate is elevated. Consider stress management techniques.")
        elif avg_hr < 60:
            insights.append("Your heart rate is lower than usual. Ensure proper hydration and activity.")
    
    # Analyze sleep patterns
    if request.sleep_patterns:
        total_sleep = sum(stage.get('duration', 0) for stage in request.sleep_patterns if isinstance(stage, dict))
        if total_sleep < 6 * 60:  # Less than 6 hours
            insights.append("You are not getting enough sleep. Aim for at least 7-8 hours per night.")
    
    # Analyze activity levels
    if request.activity_levels:
        total_steps = sum(activity.get('steps', 0) for activity in request.activity_levels if isinstance(activity, dict))
        if total_steps < 5000:
            insights.append("Your step count is low. Try increasing daily activity for better cardiovascular health.")
    
    # Analyze oxygen saturation
    if request.oxygen_saturation:
        avg_spo2 = sum(request.oxygen_saturation) / len(request.oxygen_saturation)
        if avg_spo2 < 95:
            insights.append("Your oxygen levels are slightly low. Consider deep breathing exercises.")
    
    # Analyze body temperature
    if request.temperature:
        avg_temp = sum(request.temperature) / len(request.temperature)
        if avg_temp > 37.5:
            insights.append("Your body temperature is elevated. Monitor for fever symptoms.")
    
    summary = "Wearable data analysis completed. " + ("Insights generated." if insights else "No critical issues detected.")
    
    return WearableDataResponse(
        summary=summary,
        insights=insights
    )



import requests
from app.schemas.wearables import WearableDataRequest

# ------------------------------
# Google Fit API Integration
# ------------------------------

async def fetch_google_fit_data(access_token: str) -> dict:
    url = "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Example: Last 24 hours
    from datetime import datetime, timedelta
    now = int(datetime.utcnow().timestamp() * 1000)
    yesterday = int((datetime.utcnow() - timedelta(days=1)).timestamp() * 1000)

    body = {
        "aggregateBy": [
            {"dataTypeName": "com.google.heart_rate.bpm"},
            {"dataTypeName": "com.google.step_count.delta"},
            {"dataTypeName": "com.google.sleep.segment"},
            {"dataTypeName": "com.google.oxygen_saturation"},
            {"dataTypeName": "com.google.body.temperature"}
        ],
        "bucketByTime": {"durationMillis": 86400000},
        "startTimeMillis": yesterday,
        "endTimeMillis": now
    }

    response = requests.post(url, headers=headers, json=body)
    return response.json()

def parse_google_fit_to_wearable_schema(data: dict) -> WearableDataRequest:
    heart_rate = []
    activity_levels = []
    sleep_patterns = []
    oxygen_saturation = []
    temperature = []

    for bucket in data.get("bucket", []):
        for dataset in bucket.get("dataset", []):
            for point in dataset.get("point", []):
                data_type = point.get("dataTypeName", "")
                value = point.get("value", [{}])[0].get("fpVal") or point.get("value", [{}])[0].get("intVal")

                if data_type == "com.google.heart_rate.bpm" and value:
                    heart_rate.append(value)
                elif data_type == "com.google.step_count.delta" and value:
                    activity_levels.append({"steps": value})
                elif data_type == "com.google.sleep.segment":
                    sleep_patterns.append({"duration": point.get("endTimeNanos", 0)})
                elif data_type == "com.google.oxygen_saturation" and value:
                    oxygen_saturation.append(value * 100)
                elif data_type == "com.google.body.temperature" and value:
                    temperature.append(value)

    return WearableDataRequest(
        heart_rate=heart_rate,
        activity_levels=activity_levels,
        sleep_patterns=sleep_patterns,
        oxygen_saturation=oxygen_saturation,
        temperature=temperature
    )

# ------------------------------
# Fitbit API Integration
# ------------------------------

async def fetch_fitbit_data(access_token: str) -> dict:
    headers = {"Authorization": f"Bearer {access_token}"}
    data = {}

    try:
        data["heart_rate"] = requests.get("https://api.fitbit.com/1/user/-/activities/heart/date/today/1d.json", headers=headers).json()
        data["sleep"] = requests.get("https://api.fitbit.com/1.2/user/-/sleep/date/today.json", headers=headers).json()
        data["activity"] = requests.get("https://api.fitbit.com/1/user/-/activities/date/today.json", headers=headers).json()
        data["spo2"] = requests.get("https://api.fitbit.com/1/user/-/spo2/date/today.json", headers=headers).json()
        data["temp"] = requests.get("https://api.fitbit.com/1/user/-/temp/date/today.json", headers=headers).json()
    except Exception as e:
        raise RuntimeError(f"Fitbit API call failed: {str(e)}")

    return data

def parse_fitbit_to_wearable_schema(data: dict) -> WearableDataRequest:
    heart_rate = []
    activity_levels = []
    sleep_patterns = []
    oxygen_saturation = []
    temperature = []

    try:
        for zone in data["heart_rate"]["activities-heart"][0]["value"]["heartRateZones"]:
            heart_rate.append(zone.get("min"))

        for item in data["activity"].get("summary", {}).get("activities", []):
            activity_levels.append({"steps": item.get("steps", 0)})

        for sleep in data["sleep"].get("sleep", []):
            sleep_patterns.append({"duration": sleep.get("duration", 0)})

        if "spo2" in data:
            oxygen_saturation.append(data["spo2"].get("value", 0))

        if "temp" in data:
            temperature.append(data["temp"].get("value", 0))
    except Exception as e:
        raise ValueError(f"Failed to parse Fitbit data: {str(e)}")

    return WearableDataRequest(
        heart_rate=heart_rate,
        activity_levels=activity_levels,
        sleep_patterns=sleep_patterns,
        oxygen_saturation=oxygen_saturation,
        temperature=temperature
    )
