import json
import os
from pathlib import Path
from .connection import get_connection, create_all_tables

BASE_DIR = Path(__file__).resolve().parent.parent
GARMIN_JSON_PATH = str(BASE_DIR / "data" / "training_data" / "garmin_activities.json")

def load_garmin_to_db():
    """Wciąga dane z pliku JSON Garmina do bazy SQLite."""
    if not os.path.exists(GARMIN_JSON_PATH):
        print(f"🛑 Błąd: Nie znaleziono pliku {GARMIN_JSON_PATH}!")
        return
    
    create_all_tables()
    
    conn = get_connection()
    cursor = conn.cursor()

    with open(GARMIN_JSON_PATH, 'r', encoding='utf-8') as f:
        aktywnosci = json.load(f)

    licznik_zaktualizowanych = 0

    for akt in aktywnosci:
        aktywnosc_id = str(akt.get("activityId"))
        if not aktywnosc_id or aktywnosc_id == "None":
            continue

        typ = akt.get("activityType", {}).get("typeKey", "unknown")
        nazwa = akt.get("activityName", "Nieznana aktywność")
        data_startu_raw = akt.get("startTimeLocal")
        data_startu = str(data_startu_raw) if data_startu_raw else ""
        
        dystans_m = akt.get("distance", 0)
        czas_s = akt.get("duration", 0)
        dystans_km = round(dystans_m / 1000, 2) if dystans_m else 0.0
        czas_min = round(czas_s / 60, 1) if czas_s else 0.0
        tetno_sr = int(akt.get("averageHR", 0) or 0)
        kalorie = int(akt.get("calories", 0) or 0)

        try:
            cursor.execute('''
            INSERT OR IGNORE INTO treningi 
            (aktywnosc_id, typ, nazwa, data_startu, dystans_km, czas_min, tetno_sr, kalorie)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (aktywnosc_id, typ, nazwa, data_startu, dystans_km, czas_min, tetno_sr, kalorie))
            if cursor.rowcount > 0:
                licznik_zaktualizowanych += 1
        except Exception as e:
            print(f"⚠️ Error '{nazwa}': {e}")

    conn.commit()
    conn.close()
    print(f"✅ Garmin database is up to date! Processed {licznik_zaktualizowanych} new Garmin activities.")

def fetch_unmatched_trainings_for_linker():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT aktywnosc_id, data_startu FROM treningi WHERE mecz_ID IS NULL")
    unmatched_trainings = cursor.fetchall()
    conn.close()
    return unmatched_trainings

def fetch_trainings_for_display():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM treningi WHERE mecz_ID IS NULL")
    trainings = cursor.fetchall()
    conn.close()
    return trainings