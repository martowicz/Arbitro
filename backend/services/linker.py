import sqlite3
import dotenv
import os
from datetime import datetime
from pathlib import Path

from db.repo_linker import assign_trainings_to_matches
from db.repo_matches import fetch_matches_for_linker
from db.repo_garmin import fetch_unmatched_trainings_for_linker
from db.repo_settings import get_setting

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = str(BASE_DIR / "data" / "arbitro.db")
MOJE_NAZWISKO = get_setting("surname_name")

def find_links(matches, unmatched_trainings):
    new_links = {}
    
    for match in matches: 
        try: 
            match_time = datetime.strptime(match['data_meczu'], "%Y-%m-%d %H:%M") 
        except ValueError: 
            continue 

        for training in unmatched_trainings: 
            try: 
                training_time = datetime.strptime(training['data_startu'], "%Y-%m-%d %H:%M:%S") 
            except ValueError: 
                print(f"  ⚠️ Błąd daty treningu ({training.get('nazwa', 'Brak')}): {training['data_startu']}") 
                continue 

            if match_time.date() == training_time.date(): 
                start_time_difference = (training_time - match_time).total_seconds() / 60.0 

                if -15 <= start_time_difference <= 90: 
                    new_links[training['aktywnosc_id']] = match['mecz_id']
                    print(f"🔗 Znalazłem powiązanie: {match.get('gospodarze')} - {match.get('goscie')} (Aktywność: {training['aktywnosc_id']})") 
                    
    return new_links

def run_linker(): 
    """To są nasze 'RĘCE'. Odpowiadają tylko za pobranie i zapisanie danych."""
    print("🚀 Running linker...") 
    matches = fetch_matches_for_linker(MOJE_NAZWISKO) 
    unmatched_trainings = fetch_unmatched_trainings_for_linker() 

    new_links = find_links(matches, unmatched_trainings)
    
    links = len(new_links)
    
    if links > 0:
        assign_trainings_to_matches(new_links) 
        print(f"💾 Zapisano {links} powiązań do bazy.")
    else:
        print("🤷 Brak nowych treningów do zlinkowania.")

    print(f"✅ Finished Successfully! Linked {links} Garmin activities to PZPN matches.")

if __name__ == "__main__":
    run_linker()