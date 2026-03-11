import sqlite3
import json
import os
from pathlib import Path

# Ustawienia ścieżek
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = str(BASE_DIR / "arbitro.db")
GARMIN_JSON_PATH = str(BASE_DIR / "training_data" / "garmin_activities.json")

def create_all_tables(cursor):
    """Tworzy strukturę całej bazy danych (PZPN + Garmin), jeśli jeszcze nie istnieje."""
    # Tabele PZPN
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS mecze (
        mecz_id TEXT PRIMARY KEY,
        sezon TEXT,
        runda TEXT,
        liga TEXT,
        kolejka TEXT,
        data_meczu TEXT,
        gospodarze TEXT,
        goscie TEXT,
        wynik TEXT,
        UNIQUE(data_meczu, gospodarze, goscie)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sedziowie (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        imie_nazwisko TEXT UNIQUE
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS obsady (
        mecz_id TEXT,
        sedzia_id INTEGER,
        rola TEXT,
        FOREIGN KEY (mecz_id) REFERENCES mecze(mecz_id),
        FOREIGN KEY (sedzia_id) REFERENCES sedziowie(id),
        UNIQUE(mecz_id, sedzia_id, rola) 
    )
    ''')

    # Tabela Garmin
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

# ==========================================
# SEKCJA: GARMIN DB
# ==========================================

def load_garmin_to_db():
    """Wciąga dane z pliku JSON Garmina do bazy SQLite."""
    if not os.path.exists(GARMIN_JSON_PATH):
        print(f"🛑 Błąd: Nie znaleziono pliku {GARMIN_JSON_PATH}!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    create_all_tables(cursor)

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
            INSERT OR REPLACE INTO treningi 
            (aktywnosc_id, typ, nazwa, data_startu, dystans_km, czas_min, tetno_sr, kalorie)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (aktywnosc_id, typ, nazwa, data_startu, dystans_km, czas_min, tetno_sr, kalorie))
            licznik_zaktualizowanych += 1
        except Exception as e:
            print(f"⚠️ BŁĄD ZAPISU w bazie dla '{nazwa}': {e}")

    conn.commit()
    conn.close()
    print(f"✅ Baza zaktualizowana! Przetworzono {licznik_zaktualizowanych} treningów Garmina.")

# ==========================================
# SEKCJA: PZPN DB
# ==========================================

def get_referee_id(cursor, full_name):
    """Pobiera ID sędziego z bazy lub tworzy nowe, jeśli go nie ma."""
    cursor.execute('INSERT OR IGNORE INTO sedziowie (imie_nazwisko) VALUES (?)', (full_name,))
    cursor.execute('SELECT id FROM sedziowie WHERE imie_nazwisko = ?', (full_name,))
    return cursor.fetchone()[0]

def load_known_data():
    """Wciąga z bazy to, co już znamy (ID oraz sygnatury)."""
    known_ids = set()
    known_signatures = set()
    
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT LOWER(mecz_id), data_meczu, gospodarze, goscie FROM mecze")
            for row in cursor.fetchall():
                if row[0]: known_ids.add(row[0])
                signature = f"{str(row[1]).lower()}_{str(row[2]).lower()}_{str(row[3]).lower()}"
                known_signatures.add(signature)
        except sqlite3.OperationalError:
            pass
        conn.close()
        
    return known_ids, known_signatures

def save_matches_to_db(matches):
    """Bierze pobrane mecze (z RAM-u) i wrzuca je bezpiecznie do SQLite."""
    if not matches:
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    create_all_tables(cursor)

    match_counter = 0
    for match in matches:
        url = match.get('szczegoly_url', '')
        match_id = url.split('meczId=')[-1].lower() if 'meczId=' in url else None
        
        if not match_id:
            continue

        cursor.execute('''
        INSERT OR IGNORE INTO mecze 
        (mecz_id, sezon, runda, liga, kolejka, data_meczu, gospodarze, goscie, wynik)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            match_id, match.get('sezon'), match.get('runda'), match.get('liga'),
            match.get('kolejka'), match.get('data'), match.get('gospodarze'),
            match.get('goscie'), match.get('wynik')
        ))

        referees = match.get('obsada', {})
        if isinstance(referees, dict):
            for role, full_name in referees.items():
                if full_name and full_name != "Błąd":
                    referee_id = get_referee_id(cursor, full_name)
                    cursor.execute('''
                    INSERT OR IGNORE INTO obsady (mecz_id, sedzia_id, rola)
                    VALUES (?, ?, ?)
                    ''', (match_id, referee_id, role))
                    
        match_counter += 1

    conn.commit()
    conn.close()
    print(f"✅ Zapisano {match_counter} nowych meczów prosto do bazy {DB_PATH}.")