import os
import json
from dotenv import load_dotenv
from garminconnect import Garmin
import sqlite3

import os
from pathlib import Path

# Wykrywa ścieżkę do folderu, w którym znajduje się aktualny plik .py
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = str(BASE_DIR / "arbitro.db")
GARMIN_JSON_PATH = str(BASE_DIR / "training_data" / "garmin_activities.json")

# Ładujemy zmienne z pliku .env
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)


def create_training_table(cursor):
    """Tworzy tabelę dla treningów z Garmina."""
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS treningi (
        aktywnosc_id TEXT PRIMARY KEY,
        typ TEXT,
        nazwa TEXT,
        data_startu TEXT,
        dystans_km REAL,
        czas_min REAL,
        tetno_sr INTEGER,
        kalorie INTEGER, 
        mecz_ID TEXT DEFAULT NULL,
        FOREIGN KEY (mecz_ID) REFERENCES mecze(mecz_ID)
    )
    ''')

def load_garmin_to_db():
    # Używamy ścieżki absolutnej, żeby Python zawsze znalazł właściwy plik arbitro.db
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path_absolute = os.path.join(BASE_DIR, 'arbitro.db')
    json_path_absolute = os.path.join(BASE_DIR, GARMIN_JSON_PATH)

    if not os.path.exists(json_path_absolute):
        print(f"🛑 Błąd: Nie znaleziono pliku {json_path_absolute}!")
        return

    # Otwieramy właściwą bazę
    conn = sqlite3.connect(db_path_absolute)
    cursor = conn.cursor()
    create_training_table(cursor)

    with open(json_path_absolute, 'r', encoding='utf-8') as f:
        aktywnosci = json.load(f)

    licznik_nowych = 0
    licznik_zaktualizowanych = 0

    for index, akt in enumerate(aktywnosci):
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
            # Szpieg - sprawdzamy co się dzieje z pierwszym z brzegu treningiem
            if index == 0:
                print(f"🕵️ Próbuję zapisać do bazy: {nazwa} (Dystans: {dystans_km} km)")

            # ZMIANA: REPLACE zamiast IGNORE. Zawsze mamy najświeższe dane!
            cursor.execute('''
            INSERT OR REPLACE INTO treningi 
            (aktywnosc_id, typ, nazwa, data_startu, dystans_km, czas_min, tetno_sr, kalorie)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (aktywnosc_id, typ, nazwa, data_startu, dystans_km, czas_min, tetno_sr, kalorie))
            
            licznik_zaktualizowanych += 1
            
        except Exception as e:
            print(f"⚠️ BŁĄD ZAPISU w bazie dla '{nazwa}': {e}")

    conn.commit()
    conn.close()
    
    print(f"✅ Baza zaktualizowana! Przetworzono {licznik_zaktualizowanych} treningów w pliku {db_path_absolute}.")


def scrape_garmin():
    email = os.getenv("GARMIN_EMAIL")
    haslo = os.getenv("GARMIN_PASSWORD")
    
    if not email or not haslo:
        print("🛑 Błąd: Brak danych logowania do Garmina w pliku .env!")
        return

    try:
        print("⏳ Łączenie z serwerami Garmin Connect...")
        klient = Garmin(email, haslo)
        klient.login()
        print("✅ Zalogowano pomyślnie!\n")

        limit = 100 # Możesz tu wpisać np. 100, jeśli chcesz pobrać więcej historii
        print(f"🏃 Pobieram {limit} ostatnich aktywności...")
        
        # Pobieranie surowych danych z API
        aktywnosci = klient.get_activities(0, limit)

        # --- SEKCJA ZAPISU DO JSON ---
        folder_zapis = "training_data"
        os.makedirs(folder_zapis, exist_ok=True) # Tworzy folder, jeśli go nie ma
        
        sciezka_pliku = os.path.join(folder_zapis, "garmin_activities.json")
        
        with open(sciezka_pliku, "w", encoding="utf-8") as f:
            # Zapisujemy całą surową listę słowników do pliku
            json.dump(aktywnosci, f, indent=4, ensure_ascii=False)
            
        print(f"💾 Zapisano {len(aktywnosci)} treningów do pliku: {sciezka_pliku}\n")
        print("-" * 50)
        print("Szybki podgląd ostatnich 3 aktywności:")

        # Krótki podgląd w terminalu tylko dla 3 pierwszych wyników
        for akt in aktywnosci[:3]:
            nazwa = akt.get("activityName", "Nieznana")
            data_startu = akt.get("startTimeLocal", "").split(" ")[0]
            dystans_m = akt.get("distance", 0)
            dystans_km = round(dystans_m / 1000, 2) if dystans_m else 0
            
            print(f"   ✔️ {data_startu} | {nazwa} | {dystans_km} km")
            
        print("-" * 50)
        load_garmin_to_db()

    except Exception as e:
        print(f"\n❌ Wystąpił błąd podczas pobierania danych z Garmina:\n{e}")

if __name__ == "__main__":
    scrape_garmin()