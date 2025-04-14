import openai
from openai import AsyncOpenAI
from app.core.config import settings
from app.db.session import SessionLocal
from app.crud.health_diary import get_health_diaries, get_latest_entry
from app.crud.medication import get_medications, get_today_medications
import logging
import json
import re
from typing import Dict
from datetime import datetime, timedelta

logger = logging.getLogger("ai_services")
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def analyze_symptoms(user_id: int):
    async with SessionLocal() as db:
        health_entries = await get_health_diaries(db, user_id)

    if not health_entries:
        return "No recent health entries found."

    symptom_text = ", ".join(entry.symptoms for entry in health_entries[-5:])
    prompt = f"User reported symptoms: {symptom_text}. Give a brief, direct insight."

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a concise medical AI assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Symptom analysis error: {str(e)}")
        return "Error in symptom analysis."

async def get_personalized_health_tips(user_id: int):
    async with SessionLocal() as db:
        medications = await get_medications(db, user_id)

    if not medications:
        return "No medications found."

    med_text = ", ".join(f"{med.name} ({med.dosage})" for med in medications)
    prompt = f"User is taking: {med_text}. Give short, relevant daily health tips."

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You give short health tips."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Health tips error: {str(e)}")
        return "Error generating health tips."

async def detect_health_patterns(user_id: int):
    async with SessionLocal() as db:
        entries = await get_health_diaries(db, user_id)

    if not entries or len(entries) < 2:
        return "Not enough data."

    symptoms_log = ", ".join(f"{e.date}: {e.symptoms}" for e in entries)
    prompt = f"Symptoms log: {symptoms_log}. Briefly mention any detected pattern."

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You detect patterns in symptom logs."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Pattern detection error: {str(e)}")
        return "Pattern analysis error."

async def analyze_symptom_checker(user_id: int, symptoms: list):
    if not symptoms:
        return {"error": "No symptoms provided."}

    prompt = f"Symptoms: {', '.join(symptoms)}. Return JSON with possible conditions, urgency (low/moderate/high/emergency), and next steps."

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a triage AI assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        text = re.sub(r"```json|```", "", response.choices[0].message.content.strip())
        return json.loads(text)
    except Exception as e:
        logger.error(f"Symptom checker error: {str(e)}")
        return {"error": "Symptom checker failed."}

async def generate_health_education(user_id: int, topics: list):
    if not topics:
        return "No topics provided."

    prompt = f"Give short, practical education tips about: {', '.join(topics)}."

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You give clear health education summaries."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Education generation error: {str(e)}")
        return "Education generation failed."

async def analyze_test_results(test_type: str, test_results: Dict) -> str:
    prompt = f"Test: {test_type}. Results: {json.dumps(test_results)}. Give a short insight and next step."

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You provide short, relevant diagnostic insights."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Test analysis error: {str(e)}")
        return "Test analysis failed."

async def generate_personalized_plan(db, user_id: int):
    diary = await get_latest_entry(db, user_id)
    meds = await get_today_medications(db, user_id)

    goals = ["Take your medications on time." if meds else "No meds today. Review if needed.",
             "Add a follow-up diary note." if diary else "Start your health diary.",
             "Drink at least 2L of water.",
             "Stretch or walk for 10 minutes.",
             "Log your health before bed."]

    return {"date": datetime.utcnow().date().isoformat(), "goals": goals}

def assess_mental_health_risk(mood_counts: dict, last_entry_date: datetime | None):
    risk = "low"
    reasons = []
    tip = "Keep tracking your mood."

    if not last_entry_date or (datetime.utcnow().date() - last_entry_date.date()).days >= 3:
        risk = "moderate"
        reasons.append("No recent entries.")
        tip = "Log your mood today."

    if mood_counts.get("depressed", 0) >= 3:
        risk = "high"
        reasons.append("Frequent 'depressed' entries.")
        tip = "Consider talking to someone you trust or a professional."

    return {"risk_level": risk, "reasons": reasons, "tip": tip}

async def analyze_chronic_health_data(condition, blood_pressure, blood_sugar, heart_rate, weight, medications) -> list[str]:
    bp = ", ".join(f"{b['systolic']}/{b['diastolic']}" for b in blood_pressure) if blood_pressure else "None"
    sugar = ", ".join(map(str, blood_sugar)) if blood_sugar else "None"
    hr = ", ".join(map(str, heart_rate)) if heart_rate else "None"
    wt = ", ".join(map(str, weight)) if weight else "None"
    meds = ", ".join(medications) if medications else "None"

    prompt = f"User with {condition}. BP: {bp}, Sugar: {sugar}, HR: {hr}, Weight: {wt}, Meds: {meds}. Give short bullet-point insights."

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You summarize chronic health data simply."},
                {"role": "user", "content": prompt}
            ]
        )
        insights = response.choices[0].message.content.strip().split("\n")
        return [i.strip("-• ").strip() for i in insights if i.strip()]
    except Exception as e:
        logger.error(f"Chronic data analysis error: {str(e)}")
        return ["Chronic data analysis failed."]

async def classify_emergency_type(description: str) -> tuple[str, str]:
    prompt = f"Classify: '{description}'. Type: mental health / medical / domestic violence / unknown. Give 1-line action. Return JSON."

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an emergency classifier AI."},
                {"role": "user", "content": prompt}
            ]
        )
        raw = re.sub(r"```json|```", "", response.choices[0].message.content.strip())
        data = json.loads(raw)
        return data.get("emergency_type", "unknown"), data.get("action", "Stay calm and contact emergency services.")
    except Exception as e:
        logger.error(f"Emergency classification error: {str(e)}")
        return "unknown", "Unable to classify. Contact emergency services."
