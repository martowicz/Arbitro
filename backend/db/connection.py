import sqlite3
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = str(BASE_DIR / "data" / "arbitro.db")

def get_connection() -> sqlite3.Connection:
    """Returns an active SQLite database connection. Always use this function!"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row 
    return conn

def create_all_tables():
    """Creates the entire database schema, including a new table for encrypted settings."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS mecze (
        mecz_id TEXT PRIMARY KEY,
        sezon TEXT, runda TEXT, liga TEXT, kolejka TEXT, data_meczu TEXT,
        gospodarze TEXT, goscie TEXT, wynik TEXT,
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
        mecz_id TEXT, sedzia_id INTEGER, rola TEXT,
        FOREIGN KEY (mecz_id) REFERENCES mecze(mecz_id),
        FOREIGN KEY (sedzia_id) REFERENCES sedziowie(id),
        UNIQUE(mecz_id, sedzia_id, rola) 
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS treningi (
        aktywnosc_id TEXT PRIMARY KEY,
        typ TEXT, nazwa TEXT, data_startu TEXT, dystans_km REAL,
        czas_min REAL, tetno_sr INTEGER, kalorie INTEGER, mecz_ID TEXT DEFAULT NULL,
        FOREIGN KEY (mecz_ID) REFERENCES mecze(mecz_ID)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    ''')

    conn.commit()
    conn.close()