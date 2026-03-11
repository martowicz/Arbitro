import os
from datetime import datetime
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv
from .utils import fetch_from_db, extract_garmin_hr_data, format_time
from pathlib import Path
import json

load_dotenv()
router = APIRouter(prefix="/api", tags=["Events"])

BASE_DIR = Path(__file__).resolve().parent.parent

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
            "mecz_id": match['mecz_id'],  # <--- DODAJ TĘ LINIJKĘ!
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
            "aktywnosc_id": training['aktywnosc_id'], # <--- DODAJEMY ID AKTYWNOŚCI
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


# --- ENDPOINT DLA MECZÓW (2 Wykresy) ---
@router.get("/matches/{mecz_id}/chart_data")
def get_match_chart_data(mecz_id: str):
    query = "SELECT aktywnosc_id FROM treningi WHERE mecz_id = ? ORDER BY data_startu ASC"
    results = fetch_from_db(query, (mecz_id,))
    if not results: raise HTTPException(404, "Brak przypisanych połów z Garmina.")
    
    charts = []
    for idx, row in enumerate(results):
        file_path = BASE_DIR / "training_details" / f"{row['aktywnosc_id']}.json"
        if file_path.exists():
            
            # MAGIA PRÓBKOWANIA: Możesz tu wpisać np. 15, żeby zbierać punkt co 15 sekund!
            labels, hr_data = extract_garmin_hr_data(file_path, half_number=idx+1, sample_interval_sec=10)
            
            if labels and hr_data:
                charts.append({
                    "title": f"Połowa {idx+1}", 
                    "chart": {
                        "labels": labels,
                        "datasets": [{
                            "label": "Tętno (bpm)",
                            "data": hr_data,
                            "borderColor": "#e74c3c",
                            "backgroundColor": "rgba(231, 76, 60, 0.2)",
                            "fill": True,
                            "tension": 0.4,
                            "pointRadius": 1 # Przy gęstym próbkowaniu zmniejszamy kropki z 2 na 1
                        }]
                    }
                })
                
    if not charts: raise HTTPException(404, "Pliki są puste.")
    return charts

# --- ENDPOINT DLA TRENINGÓW (1 Wykres) ---
@router.get("/trainings/{aktywnosc_id}/chart_data")
def get_training_chart_data(aktywnosc_id: str):
    file_path = BASE_DIR / "training_details" / f"{aktywnosc_id}.json"
    if not file_path.exists(): raise HTTPException(404, "Brak pliku treningu.")
    
    # Dla zwykłych treningów też ustawiamy interwał (np. 30 sekund)
    labels, hr_data = extract_garmin_hr_data(file_path, half_number=None, sample_interval_sec=10)
    
    if not labels or not hr_data: 
        raise HTTPException(404, "Brak tętna w pliku.")
    
    return [{
        "title": "Tętno z treningu", 
        "chart": {
            "labels": labels,
            "datasets": [{
                "label": "Tętno (bpm)",
                "data": hr_data,
                "borderColor": "#e74c3c",
                "backgroundColor": "rgba(231, 76, 60, 0.2)",
                "fill": True,
                "tension": 0.4,
                "pointRadius": 1
            }]
        }
    }]