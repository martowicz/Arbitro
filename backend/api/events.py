import os
from datetime import datetime
from fastapi import APIRouter
from dotenv import load_dotenv
from .utils import format_time
from pathlib import Path

from .models import Event
from typing import List
from db.repo_garmin import fetch_trainings_for_display
from db.repo_matches import fetch_matches_for_display
from db.repo_settings import get_setting

load_dotenv()
router = APIRouter(prefix="/api", tags=["Events"])

BASE_DIR = Path(__file__).resolve().parent.parent

@router.get("/events", response_model=List[Event])
def get_events():
    """Fetches all matched matches and unlinked trainings to build the timeline."""
    events = []
    REFEREE_NAME = get_setting("surname_name")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    matches_data = fetch_matches_for_display(REFEREE_NAME)

    for match in matches_data:
        category = "past_matches" if match['data_meczu'] < current_time else "upcoming_matches"
        
        events.append({
                "match_id": match['mecz_id'],
                "entry_type": category,
                "date": match['data_meczu'], 
                "title": f"⚽ {match['gospodarze']} - {match['goscie']}",
                "subtitle": f"{match['liga']} | {match['rola']}", 
                "distance": match['full_distance'] or 0.0, 
                "heart_rate": match['average_heart_rate'] or 0.0, 
                "calories": match['full_calories'] or 0.0, 
                "time": format_time(match['full_time']) if match['full_time'] else "00:00"
            })

    trainings_data = fetch_trainings_for_display()
    
    for training in trainings_data:
        emoji = "🏃" if training['typ'] == "running" else "🚴" if training['typ'] == "cycling" else "💪"

        events.append({
                "activity_id": training['aktywnosc_id'],
                "entry_type": "training",
                "date": str(training['data_startu'])[:16], 
                "title": f"{emoji} {training['nazwa']}",
                "subtitle": f"Trening | ⏱️ {training['czas_min']} min", 
                "distance": training['dystans_km'],
                "heart_rate": training['tetno_sr'], 
                "calories": training['kalorie'], 
                "time": format_time(training['czas_min'])
            })

    #sorting by date descending
    events.sort(key=lambda item: item['date'], reverse=True)

    return events