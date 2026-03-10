import os
from datetime import datetime
from fastapi import APIRouter
from dotenv import load_dotenv
from .utils import fetch_from_db, format_time

load_dotenv()
router = APIRouter(prefix="/api", tags=["Events"])

@router.get("/events")
def get_events():
    """Fetches all matched matches and unlinked trainings to build the timeline."""
    events = []
    REFEREE_NAME = os.getenv("SURNAME_NAME")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 1. FETCH MATCHES
    matches_query = '''
        SELECT m.mecz_id, m.data_meczu, m.gospodarze, m.goscie, m.liga, o.rola,
               SUM(t.dystans_km) as full_distance, SUM(t.czas_min) as full_time, 
               ROUND(AVG(t.tetno_sr)) as average_heart_rate, SUM(t.kalorie) as full_calories
        FROM mecze m
        JOIN obsady o ON m.mecz_id = o.mecz_id
        JOIN sedziowie s ON o.sedzia_id = s.id
        LEFT JOIN treningi t ON m.mecz_id = t.mecz_id
        WHERE s.imie_nazwisko = ?
        GROUP BY m.mecz_id
    '''
    matches_data = fetch_from_db(matches_query, (REFEREE_NAME,))

    for match in matches_data:
        category = "past_matches" if match['data_meczu'] < current_time else "upcoming_matches"
        
        events.append({
            "typ_wpisu": category,
            "data": match['data_meczu'], 
            "tytul": f"⚽ {match['gospodarze']} - {match['goscie']}",
            "podtytul": f"{match['liga']} | {match['rola']}", 
            "dystans": match['full_distance'], 
            "tetno": match['average_heart_rate'], 
            "kalorie": match['full_calories'], 
            "sort_date": match['data_meczu'],
            "time": format_time(match['full_time'])
        })

    # 2. FETCH TRAININGS (unlinked)
    trainings_query = 'SELECT * FROM treningi WHERE mecz_id IS NULL'
    trainings_data = fetch_from_db(trainings_query)
    
    for training in trainings_data:
        emoji = "🏃" if training['typ'] == "running" else "🚴" if training['typ'] == "cycling" else "💪"

        events.append({
            "typ_wpisu": "training",
            "data": str(training['data_startu'])[:16], 
            "tytul": f"{emoji} {training['nazwa']}",
            "podtytul": f"Trening | ⏱️ {training['czas_min']} min", 
            "dystans": training['dystans_km'],
            "tetno": training['tetno_sr'], 
            "kalorie": training['kalorie'], 
            "sort_date": training['data_startu'],
            "time": format_time(training['czas_min'])
        })

    # 3. SORT EVENTS DESCENDING
    events.sort(key=lambda item: item['sort_date'], reverse=True)

    return events