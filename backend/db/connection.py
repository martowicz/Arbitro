import sqlite3
from pathlib import Path

# Ścieżki wyliczane raz, poprawnie dla całego projektu
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = str(BASE_DIR / "data" / "arbitro.db")

def get_connection() -> sqlite3.Connection:
    """Zwraca aktywne połączenie z bazą danych SQLite. Zawsze używaj tej funkcji!"""
    # check_same_thread=False jest przydatne dla FastAPI
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    # Pozwala odwoływać się do kolumn po nazwach (np. row['mecz_id'])
    conn.row_factory = sqlite3.Row 
    return conn

def create_all_tables():
    """Tworzy strukturę całej bazy danych, w tym nową tabelę na zaszyfrowane ustawienia."""
    conn = get_connection()
    cursor = conn.cursor()

    # Tabele PZPN
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

    # Tabela Garmin
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS treningi (
        aktywnosc_id TEXT PRIMARY KEY,
        typ TEXT, nazwa TEXT, data_startu TEXT, dystans_km REAL,
        czas_min REAL, tetno_sr INTEGER, kalorie INTEGER, mecz_ID TEXT DEFAULT NULL,
        FOREIGN KEY (mecz_ID) REFERENCES mecze(mecz_ID)
    )
    ''')

    # Nasza NOWA Tabela do Etapu 2 (Szyfrowanie AES)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ustawienia (
        klucz TEXT PRIMARY KEY,
        wartosc TEXT
    )
    ''')

    conn.commit()
    conn.close()