# Plik: api/match.py
from fastapi import APIRouter, BackgroundTasks
import subprocess
import sys
from .utils import pobierz_z_bazy, run_script, SYNC_STATE, BASE_DIR, time_transform
import os
from dotenv import load_dotenv
# Tworzymy router dla tej sekcji
router = APIRouter(prefix="/api")
load_dotenv()

from datetime import datetime

@router.get("/events")
def get_events():
    events = [] # Jeden wspólny worek na wszystko
    MOJE_NAZWISKO = os.getenv("SURNAME_NAME") 
    
    # Pobieramy obecny czas w formacie pasującym do bazy (YYYY-MM-DD HH:MM)
    teraz = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 1. POBIERAMY WSZYSTKIE MECZE
    mecze = pobierz_z_bazy('''
        SELECT m.mecz_id, m.data_meczu, m.gospodarze, m.goscie, m.liga, o.rola,
               SUM(t.dystans_km) as full_distance, SUM(t.czas_min) as full_time, ROUND(AVG(t.tetno_sr)) as average_heart_rate, SUM(t.kalorie) as full_calories
        FROM mecze m
        JOIN obsady o ON m.mecz_id = o.mecz_id
        JOIN sedziowie s ON o.sedzia_id = s.id
        LEFT JOIN treningi t ON m.mecz_id = t.mecz_id
        WHERE s.imie_nazwisko = ?
        GROUP BY m.mecz_id
    ''', (MOJE_NAZWISKO,))

    for m in mecze:
        # Decydujemy, czy mecz jest z przeszłości, czy z przyszłości
        kategoria = "past_matches" if m['data_meczu'] < teraz else "upcoming_matches"
        raw_time = m['full_time']
        display_time = time_transform(raw_time) if (raw_time and raw_time > 3) else "0:00"
        
        events.append({
            "typ_wpisu": kategoria, # Wrzucamy odpowiednią kategorię
            "data": m['data_meczu'], 
            "tytul": f"⚽ {m['gospodarze']} - {m['goscie']}",
            "podtytul": f"{m['liga']} | {m['rola']}", 
            "dystans": m['full_distance'], 
            "tetno": m['average_heart_rate'], 
            "kalorie": m['full_calories'], 
            "sort_date": m['data_meczu'],
            "time" : display_time
        })

    # 2. POBIERAMY TRENINGI
    treningi = pobierz_z_bazy('SELECT * FROM treningi WHERE mecz_id IS NULL')
    
    for t in treningi:
        emoji = "🏃" if t['typ'] == "running" else "🚴" if t['typ'] == "cycling" else "💪"

        raw_t_time = t['czas_min']
        display_t_time = time_transform(raw_t_time) if (raw_t_time and raw_t_time > 3) else "0:00"

        events.append({
            "typ_wpisu": "training", # Wrzucamy kategorię treningu
            "data": str(t['data_startu'])[:16], 
            "tytul": f"{emoji} {t['nazwa']}",
            "podtytul": f"Trening | ⏱️ {t['czas_min']} min", 
            "dystans": t['dystans_km'],
            "tetno": t['tetno_sr'], 
            "kalorie": t['kalorie'], 
            "sort_date": t['data_startu'],
            "time" : display_t_time
        })

    # 3. SORTUJEMY WSZYSTKO "JAK LECI" (Malejąco - najnowsze i przyszłe na samej górze)
    events.sort(key=lambda x: x['sort_date'], reverse=True)

    return events

@router.post("/sync/pzpn")
def sync_pzpn(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_script, "scraper_pzpn.py")
    return {"status": "started", "message": "Synchronizacja PZPN ruszyła w tle."}

@router.get("/sync/status")
def get_sync_status():
    return {"is_syncing": SYNC_STATE["is_syncing"]}

@router.post("/pobierz_dane")
def uruchom_pobieranie_danych():
    try:
        subprocess.run([sys.executable, "scraper_pzpn.py"], check=True, cwd=str(BASE_DIR))
        subprocess.run([sys.executable, "scraper_garmin.py"], check=True, cwd=str(BASE_DIR))
        subprocess.run([sys.executable, "linker.py"], check=True, cwd=str(BASE_DIR))
        return {"status": "sukces", "wiadomosc": "Pomyślnie pobrano i zsynchronizowano dane!"}
    except Exception as e:
        return {"status": "blad", "wiadomosc": f"Błąd serwera: {e}"}