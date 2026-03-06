import os
import json
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import sqlite3

load_dotenv()

CURRENT_SEASON = "2025/2026" # Ustaw swój sezon docelowy
import os
from pathlib import Path

# Wykrywa ścieżkę do folderu, w którym znajduje się aktualny plik .py
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = str(BASE_DIR / "arbitro.db")
GARMIN_JSON = str(BASE_DIR / "training_data" / "garmin_activities.json")


# ==========================================
# SEKCJA 1: BAZA DANYCH (SQLITE)
# ==========================================

def create_tables(cursor):
    """Tworzy strukturę bazy danych, jeśli jeszcze nie istnieje."""
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
    create_tables(cursor)

    match_counter = 0
    for match in matches:
        url = match.get('szczegoly_url', '')
        match_id = url.split('meczId=')[-1].lower() if 'meczId=' in url else None
        
        if not match_id:
            continue

        # Wrzucamy mecz
        cursor.execute('''
        INSERT OR IGNORE INTO mecze 
        (mecz_id, sezon, runda, liga, kolejka, data_meczu, gospodarze, goscie, wynik)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            match_id, match.get('sezon'), match.get('runda'), match.get('liga'),
            match.get('kolejka'), match.get('data'), match.get('gospodarze'),
            match.get('goscie'), match.get('wynik')
        ))

        # Wrzucamy sędziów z obsady
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


# ==========================================
# SEKCJA 2: PLIKI LOKALNE (JSON)
# ==========================================

def save_season_to_json(season, new_matches):
    """Zapisuje dane do pliku JSON w folderze match_data."""
    if not new_matches: return
    
    # Tworzymy folder, jeśli nie istnieje
    os.makedirs('match_data', exist_ok=True)
    
    file_name = f"match_data/season_{season.replace('/', '_')}.json"
    old_data = []
    
    if os.path.exists(file_name):
        with open(file_name, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
            
    old_data.extend(new_matches)
    
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(old_data, f, indent=4, ensure_ascii=False)
    print(f"  💾 Zaktualizowano plik JSON: {file_name}")


# ==========================================
# SEKCJA 3: SCRAPING (PLAYWRIGHT)
# ==========================================

def extract_table_data(page, season, round_name, known_ids, known_signatures):
    """Zwraca TYLKO nowe mecze z aktualnie widocznej tabeli."""
    new_matches = []
    rows = page.query_selector_all("#spotkania_tabela tbody tr")
    
    for row in rows:
        cols = row.query_selector_all("td")
        if len(cols) > 5:
            match_id = cols[-1].text_content().strip().lower()
            
            match_date = cols[4].inner_text().strip()
            home_team = cols[5].inner_text().strip()
            away_team = cols[6].inner_text().strip()
            
            # Unikalna sygnatura zapobiegająca dublom
            signature = f"{match_date.lower()}_{home_team.lower()}_{away_team.lower()}"
            
            if match_id in known_ids or signature in known_signatures:
                continue

            details_url = f"https://pzpn24.pzpn.pl/Ogolne/Obsady/Spotkanie?meczId={match_id}"

            match_entry = {
                "sezon": season,
                "runda": round_name,
                "liga": cols[0].inner_text().strip(),
                "kolejka": cols[3].inner_text().strip(),
                "data": match_date,
                "gospodarze": home_team,
                "goscie": away_team,
                "wynik": cols[8].inner_text().strip(),
                "szczegoly_url": details_url,
                "obsada": {} 
            }
            new_matches.append(match_entry)
            
            known_ids.add(match_id)
            known_signatures.add(signature)
            
    return new_matches

def scrape_arbitro(current_season, is_new_user, known_ids=None, known_signatures=None):
    """Główny silnik pobierający dane TYLKO dla wskazanego sezonu."""
    known_ids = known_ids or set()
    known_signatures = known_signatures or set()
    all_new_matches = []

    if is_new_user:
        print(f"🆕 WYKRYTO NOWEGO UŻYTKOWNIKA. Rozpoczynam pełne pobieranie dla sezonu {current_season}...")
    else:
        print(f"🔄 ZNANY UŻYTKOWNIK. Szukam tylko nowych meczów dla sezonu {current_season}...")

    # with sync_playwright() as p:
    #     browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
    #     context = browser.new_context(viewport={'width': 1280, 'height': 720})
    #     page = context.new_page()

    #     print("🚀 Otwieram stronę logowania PZPN24...")
    #     page.goto("https://pzpn24.pzpn.pl/Login")
        
    #     input("👉 Zaloguj się RĘCZNIE i po zobaczeniu panelu wciśnij ENTER... ")
    with sync_playwright() as p:
        # headless=False zostawiamy, żebyś widział jak bot pracuje, 
        # ale zmieniamy sposób logowania
        browser = p.chromium.launch(headless=False) 
        context = browser.new_context()
        page = context.new_page()

        print("🚀 Automatyczne logowanie do PZPN24...")
        page.goto("https://pzpn24.pzpn.pl/Login")
        
        # WPISYWANIE DANYCH Z .ENV
        page.fill("input#username", os.getenv("PZPN_EMAIL"))
        page.fill("input#password", os.getenv("PZPN_PASS"))
        
        # Kliknięcie przycisku logowania (selektor może się różnić, sprawdź go w przeglądarce)
        page.click("input#kc-login")
        try:
            print("🍪 Sprawdzam baner cookies...")
            # Czekamy max 5 sekund na przycisk i klikamy go
            page.click("button[data-testid='uc-accept-all-button']", timeout=5000)
            print("🍪 Ciasteczka zaakceptowane!")
        except:
            print("🍪 Baner cookies nie wyskoczył. Lecimy dalej.")
        
        # Czekamy na załadowanie panelu (np. na widoczność menu)
        page.wait_for_load_state("networkidle")
        print("✅ Logowanie zakończone (oczekiwanie na załadowanie panelu).")
        user_menu = page.locator(".navbar-right .dropdown-toggle").first
        if user_menu.is_visible() and "SĘDZIA" not in user_menu.inner_text().upper():
            print(f"   🔄 Przełączam na profil Sędziego...")
            user_menu.click()
            time.sleep(1)
            referee_option = page.locator(".navbar-right .dropdown-menu a", has_text="- Sędzia").first
            if referee_option.is_visible():
                referee_option.click()
                page.wait_for_load_state("networkidle")
                time.sleep(1)

        page.get_by_role("link", name="Judge", exact=False).click()
        page.wait_for_timeout(500)
        page.click('a[href="/Ogolne/Obsady"]')
        page.wait_for_load_state("networkidle")

        page.select_option("#SezonFiltr", current_season)
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        rounds = {"Jesienna": "1", "Wiosenna": "2"}
        
        for round_name, round_val in rounds.items():
            print(f"  🍂 Runda: {round_name}")
            page.select_option("#RundaFiltr", round_val)
            page.wait_for_load_state("networkidle")
            time.sleep(1)
            
            while True:
                new_on_page = extract_table_data(page, current_season, round_name, known_ids, known_signatures)
                all_new_matches.extend(new_on_page)
                
                next_btn = page.locator("#spotkania_tabela_next")
                if next_btn.is_visible() and "disabled" not in (next_btn.get_attribute("class") or ""):
                    next_btn.click()
                    time.sleep(1)
                    continue
                break

        if not all_new_matches:
            print(f"  ✅ Brak nowych meczów w sezonie {current_season}.")
        else:
            print(f"  🔍 Wchodzę w szczegóły {len(all_new_matches)} NOWYCH meczów...")
            
            for match in all_new_matches:
                try:
                    page.goto(match["szczegoly_url"])
                    page.wait_for_load_state("networkidle")
                    
                    referees_link = page.locator('a[href="#obsada"]')
                    if referees_link.is_visible():
                        referees_link.click()
                        time.sleep(0.5) 
                        
                        referees_details = {}
                        referee_blocks = page.locator("#obsada .panel-default").all()
                        for block in referee_blocks:
                            role = block.locator(".panel-heading").inner_text().strip()
                            name_input = block.locator("input[id$='_Nazwa']")
                            if name_input.count() == 0:
                                name_input = block.locator("input[type='text']").first
                            if name_input.is_visible():
                                full_name = name_input.input_value().strip()
                                if full_name:
                                    referees_details[role] = full_name
                        match["obsada"] = referees_details
                    print(f"     ✔️ Pomyślnie pobrano obsadę: {match['gospodarze']} vs {match['goscie']}")
                except Exception as e:
                    print(f"     ❌ Błąd dla {match['gospodarze']} vs {match['goscie']}: {e}")
            
            # Zapisujemy JSON w trakcie działania scrapera
            save_season_to_json(current_season, all_new_matches)

        print(f"\n🎉 ZAKOŃCZONO! Zabrano {len(all_new_matches)} nowych meczów.")
        browser.close()
        
        return all_new_matches


# ==========================================
# SEKCJA 4: GŁÓWNY PUNKT WEJŚCIA (ENTRY POINT)
# ==========================================

def run_scraper(current_season=CURRENT_SEASON):
    print(f"⚽ ARBITRO SYSTEM START - Sezon {current_season}")
    
    known_ids, known_signatures = load_known_data()
    is_new_user = len(known_ids) == 0

    new_matches = scrape_arbitro(
        current_season=current_season, 
        is_new_user=is_new_user, 
        known_ids=known_ids, 
        known_signatures=known_signatures
    )
    
    if new_matches:
        print(f"📥 Rozpoczynam zapisywanie pobranych danych do bazy SQLite...")
        save_matches_to_db(new_matches)
    else:
        print("👍 Wszystko jest aktualne, brak nowych meczów do dodania do bazy.")
if __name__ == "__main__":
    run_scraper()