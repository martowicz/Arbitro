import sqlite3
import dotenv
import os
from datetime import datetime
from pathlib import Path

dotenv.load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = str(BASE_DIR / "data" / "arbitro.db")
MOJE_NAZWISKO = os.getenv("SURNAME_NAME")

def run_linker():
    print("🚀 Uruchamiam zoptymalizowany system łączenia danych...")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Wyciągamy mecze użytkownika
    cursor.execute('''
        SELECT m.mecz_id, m.data_meczu, m.liga, m.gospodarze, m.goscie 
        FROM mecze m
        JOIN obsady o ON m.mecz_id = o.mecz_id
        JOIN sedziowie s ON o.sedzia_id = s.id
        WHERE s.imie_nazwisko = ?
    ''', (MOJE_NAZWISKO,))
    mecze = cursor.fetchall()

    # 2. Wyciągamy tylko te treningi biegowe, które jeszcze nie są przypisane do żadnego meczu
    cursor.execute("SELECT aktywnosc_id, data_startu FROM treningi WHERE typ IN ('running') AND mecz_ID IS NULL")
    treningi = cursor.fetchall()

    if not mecze or not treningi:
        print("✅ Brak nowych danych do zlinkowania.")
        conn.close()
        return

    zlinkowane_polowy = 0

    # 3. Logika łączenia (Szukamy pasujących czasów)
    for mecz in mecze:
        # Zamieniamy tekst z bazy na obiekt daty do obliczeń
        try:
            mecz_czas = datetime.strptime(mecz['data_meczu'], "%Y-%m-%d %H:%M")
        except ValueError:
            continue # Pomijamy, jeśli data w bazie jest uszkodzona

        for trening in treningi:
            try:
                # Garmin zapisuje daty z sekundami: "%Y-%m-%d %H:%M:%S"
                trening_czas = datetime.strptime(trening['data_startu'], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                print(f"  ⚠️ Błąd daty treningu ({trening['nazwa']}): {trening['data_startu']}")
                continue

            # Sprawdzamy, czy to ten sam dzień
            if mecz_czas.date() == trening_czas.date():
                # Różnica w minutach
                roznica_minut = (trening_czas - mecz_czas).total_seconds() / 60.0

                # Jeśli trening zaczął się do 15 min przed meczem lub do 120 min po rozpoczęciu:
                if -15 <= roznica_minut <= 120:
                    cursor.execute("""
                        UPDATE treningi 
                        SET mecz_id = ? 
                        WHERE aktywnosc_id = ?
                    """, (mecz['mecz_id'], trening['aktywnosc_id']))
                    
                    zlinkowane_polowy += 1
                    print(f"🔗 Zlinkowano połowę do meczu: {mecz['gospodarze']} - {mecz['goscie']}")

    # 4. Zapisujemy zmiany w bazie
    conn.commit()
    conn.close()
    
    print(f"✅ Zakończono! Przypisano {zlinkowane_polowy} aktywności z Garmina do meczów PZPN.")

if __name__ == "__main__":
    run_linker()