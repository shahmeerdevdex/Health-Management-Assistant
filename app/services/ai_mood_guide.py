from openai import AsyncOpenAI
from app.core.config import settings
import logging
import json
import random
from collections import Counter, defaultdict
from datetime import datetime

logger = logging.getLogger("ai_services")
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def analyze_mental_health(user_input):
    """AI-driven mental health analysis (concise and categorized)."""
    insights = []
    recommendations = []

    if user_input.mood_logs and user_input.health_data:
        prompt = f"Moods: {user_input.mood_logs}\nHealth: {user_input.health_data}. Briefly connect them in under 20 words."
        response = await ai_request(prompt, "Mood-Health Link")
        insights.append(response)
        recommendations.append(response["insight"])

    if user_input.mood_board:
        prompt = f"Mood board: {user_input.mood_board}. Describe tone in one concise sentence."
        response = await ai_request(prompt, "Mood Board Summary")
        insights.append(response)
        recommendations.append(response["insight"])

    if user_input.mood_logs and user_input.health_data:
        prompt = "Stress may persist. Use daily mindful breathing to stay calm."
        response = await ai_request(prompt, "Mental Health Forecast")
        insights.append(response)
        recommendations.append(response["insight"])

    if user_input.mood_logs:
        prompt = (
            "Provide brief daily tasks for moods: "

            "Anxious: Breathe 5 mins, short walk."

            "Tired: Nap 20 mins, hydrate/stretch."

            "Motivated: Set goal, start a delayed task."
        )
        response = await ai_request(prompt, "Action Plan")
        insights.append(response)
        recommendations.append(response["insight"])

    if user_input.social_interactions:
        prompt = f"Social logs: {user_input.social_interactions}. Which interaction likely helped mood most? Answer in one line."
        response = await ai_request(prompt, "Social Check-In")
        insights.append(response)
        recommendations.append(response["insight"])

    if user_input.goals_progress:
        prompt = f"Goal progress: {user_input.goals_progress}. Suggest a small improvement in one line."
        response = await ai_request(prompt, "Goal Feedback")
        insights.append(response)
        recommendations.append(response["insight"])

    insights.append(await ai_request("Summarize mood in one line.", "Mood Summary"))

    if user_input.mood_logs:
        feeling = random.choice(user_input.mood_logs)
        prompt = f"Feeling {feeling}. Suggest one media/content to lift mood."
        response = await ai_request(prompt, "Support Content")
        insights.append(response)
        recommendations.append(response["insight"])

    response = await ai_request("Rate resilience 1–5 with reason, in 15 words max.", "Resilience Score")
    insights.append(response)
    recommendations.append(response["insight"])

    response = await ai_request("Mood stability improves with sleep. Aim for 7–9 hours nightly.", "Mood Prediction")
    insights.append(response)
    recommendations.append(response["insight"])

    response = await ai_request(
        "Best habits for the day: Morning: hydrate, meditate, set goals. Afternoon: walk, eat, review. Evening: unplug, reflect, prep.",
        "Time Mood Trends"
    )
    insights.append(response)
    recommendations.append(response["insight"])

    response = await ai_request("Self-compassion: treat yourself like a friend. Suggest 1 tip.", "Self-Compassion Tip")
    insights.append(response)
    recommendations.append(response["insight"])

    return {
        "user_id": user_input.user_id,
        "insights": insights,
        "recommendations": recommendations
    }

async def ai_request(prompt: str, category: str):
    """Send simplified prompt to OpenAI."""
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a concise mental health AI. Respond briefly and to the point. No emojis."},
                {"role": "user", "content": prompt}
            ]
        )
        return {"category": category, "insight": response.choices[0].message.content.strip()}
    except Exception as e:
        logger.error(f"AI error in {category}: {str(e)}")
        return {"category": category, "insight": "AI processing failed."}

async def get_time_of_day(hour: int) -> str:
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    else:
        return "evening"

async def analyze_mood_patterns(mood_entries: list[tuple[datetime, int]]) -> dict:
    mood_by_time = defaultdict(list)
    all_moods = []

    mood_scale = {
        1: "very sad",
        2: "sad",
        3: "neutral",
        4: "happy",
        5: "very happy"
    }

    for timestamp, mood_value in mood_entries:
        mood_label = mood_scale.get(mood_value, "neutral")
        time_block = await get_time_of_day(timestamp.hour)
        mood_by_time[time_block].append(mood_label)
        all_moods.append(mood_label)

    trend = {
        period: Counter(moods).most_common(1)[0][0]
        for period, moods in mood_by_time.items()
    }

    avatar_map = {
        "very happy": ":)",
        "happy": ":)",
        "neutral": ":|",
        "sad": ":(",
        "very sad": ":("  # Kept simple instead of emojis
    }

    most_common_mood = Counter(all_moods).most_common(1)[0][0]
    avatar = avatar_map.get(most_common_mood, ":)")

    return {
        "mood_avatar": avatar,
        "most_common_mood": most_common_mood,
        "time_of_day_trend": trend
    }
