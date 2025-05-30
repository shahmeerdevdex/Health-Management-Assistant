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
    hourly_moods = defaultdict(list)

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
        hourly_moods[timestamp.hour].append(mood_value)
        all_moods.append(mood_label)

    # Enhanced time-of-day analysis
    time_trend = {
        period: {
            "dominant_mood": Counter(moods).most_common(1)[0][0],
            "mood_distribution": dict(Counter(moods)),
            "average_mood": sum(mood_scale.get(m, 3) for m in moods) / len(moods) if moods else 3
        }
        for period, moods in mood_by_time.items()
    }

    # Hourly mood patterns
    hourly_patterns = {
        hour: {
            "average": sum(moods) / len(moods) if moods else 3,
            "count": len(moods)
        }
        for hour, moods in hourly_moods.items()
    }

    # Enhanced avatar system
    avatar_map = {
        "very happy": {"text": ":)", "color": "#4CAF50", "description": "Radiating positivity"},
        "happy": {"text": ":)", "color": "#8BC34A", "description": "Feeling good"},
        "neutral": {"text": ":|", "color": "#FFC107", "description": "Balanced and centered"},
        "sad": {"text": ":(", "color": "#FF9800", "description": "Feeling down"},
        "very sad": {"text": ":(", "color": "#F44336", "description": "Having a tough time"}
    }

    most_common_mood = Counter(all_moods).most_common(1)[0][0]
    avatar = avatar_map.get(most_common_mood, avatar_map["neutral"])

    # Calculate self-compassion score
    self_compassion_score = calculate_self_compassion_score(mood_entries, time_trend)

    return {
        "mood_avatar": avatar,
        "most_common_mood": most_common_mood,
        "time_of_day_trend": time_trend,
        "hourly_patterns": hourly_patterns,
        "self_compassion_score": self_compassion_score,
        "mood_stability": calculate_mood_stability(mood_entries)
    }

def calculate_self_compassion_score(mood_entries: list[tuple[datetime, int]], time_trend: dict) -> dict:
    """Calculate self-compassion score based on mood patterns and recovery."""
    if not mood_entries:
        return {"score": 0, "factors": [], "suggestions": []}

    # Calculate mood recovery rate
    recovery_events = 0
    total_downturns = 0
    
    for i in range(1, len(mood_entries)):
        prev_mood = mood_entries[i-1][1]
        curr_mood = mood_entries[i][1]
        if prev_mood < 3 and curr_mood > prev_mood:
            recovery_events += 1
        if prev_mood > curr_mood:
            total_downturns += 1

    recovery_rate = recovery_events / total_downturns if total_downturns > 0 else 1

    # Calculate mood stability
    mood_values = [entry[1] for entry in mood_entries]
    mood_stability = 1 - (max(mood_values) - min(mood_values)) / 4

    # Calculate time-based consistency
    time_consistency = sum(
        trend["average_mood"] > 3 for trend in time_trend.values()
    ) / len(time_trend)

    # Calculate final score (0-100)
    score = int((recovery_rate * 0.4 + mood_stability * 0.3 + time_consistency * 0.3) * 100)

    factors = []
    if recovery_rate > 0.7:
        factors.append("Strong mood recovery")
    if mood_stability > 0.7:
        factors.append("Good mood stability")
    if time_consistency > 0.7:
        factors.append("Consistent positive moods")

    suggestions = []
    if recovery_rate < 0.5:
        suggestions.append("Practice self-compassion exercises")
    if mood_stability < 0.5:
        suggestions.append("Try mindfulness techniques")
    if time_consistency < 0.5:
        suggestions.append("Establish daily positive routines")

    return {
        "score": score,
        "factors": factors,
        "suggestions": suggestions
    }

def calculate_mood_stability(mood_entries: list[tuple[datetime, int]]) -> dict:
    """Calculate mood stability metrics."""
    if not mood_entries:
        return {"stability_score": 0, "volatility": 0, "trend": "neutral"}

    mood_values = [entry[1] for entry in mood_entries]
    avg_mood = sum(mood_values) / len(mood_values)
    
    # Calculate volatility (standard deviation)
    squared_diff_sum = sum((m - avg_mood) ** 2 for m in mood_values)
    volatility = (squared_diff_sum / len(mood_values)) ** 0.5

    # Calculate trend
    if len(mood_values) >= 2:
        first_half = mood_values[:len(mood_values)//2]
        second_half = mood_values[len(mood_values)//2:]
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        trend = "improving" if second_avg > first_avg else "declining" if second_avg < first_avg else "stable"
    else:
        trend = "neutral"

    # Calculate stability score (0-100)
    stability_score = int((1 - min(volatility / 2, 1)) * 100)

    return {
        "stability_score": stability_score,
        "volatility": volatility,
        "trend": trend,
        "average_mood": avg_mood
    }
