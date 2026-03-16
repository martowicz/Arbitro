import os
import json
import time
from playwright.sync_api import sync_playwright
from pathlib import Path
# <--- IMPORTY Z BAZY:
from db.repo_matches import load_known_data, save_matches_to_db
from db.repo_settings import get_setting
from core.security import decrypt_data

BASE_DIR = Path(__file__).resolve().parent.parent
CURRENT_SEASON = "2025/2026"

def save_season_to_json(season, new_matches):
    """Zapisuje dane do pliku JSON w folderze match_data."""
    if not new_matches: return
    
    # 1. Definiujemy docelowy folder z użyciem Pathlib
    target_folder = BASE_DIR / "data" / "match_data"
    
    # 2. Tworzymy folder WRAZ ze wszystkimi folderami nadrzędnymi (jeśli nie istnieją)
    target_folder.mkdir(parents=True, exist_ok=True)
    
    file_name = target_folder / f"season_{season.replace('/', '_')}.json"
    old_data = []
    
    if file_name.exists():
        with open(file_name, 'r', encoding='utf-8') as f:
            try:
                old_data = json.load(f)
            except json.JSONDecodeError:
                old_data = []
            
    old_data.extend(new_matches)
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(old_data, f, indent=4, ensure_ascii=False)
    print(f"  💾 Zaktualizowano plik JSON: {file_name}")

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
            
            signature = f"{match_date.lower()}_{home_team.lower()}_{away_team.lower()}"
            
            if match_id in known_ids or signature in known_signatures:
                continue

            details_url = f"https://pzpn24.pzpn.pl/Ogolne/Obsady/Spotkanie?meczId={match_id}"
            match_entry = {
                "sezon": season, "runda": round_name, "liga": cols[0].inner_text().strip(),
                "kolejka": cols[3].inner_text().strip(), "data": match_date,
                "gospodarze": home_team, "goscie": away_team, "wynik": cols[8].inner_text().strip(),
                "szczegoly_url": details_url, "obsada": {} 
            }
            new_matches.append(match_entry)
            known_ids.add(match_id)
            known_signatures.add(signature)
            
    return new_matches

def scrape_arbitro(current_season, is_new_user, known_ids=None, known_signatures=None):
    known_ids = known_ids or set()
    known_signatures = known_signatures or set()
    all_new_matches = []

    if is_new_user: print(f"🆕 WYKRYTO NOWEGO UŻYTKOWNIKA. Rozpoczynam pełne pobieranie dla sezonu {current_season}...")
    else: print(f"🔄 ZNANY UŻYTKOWNIK. Szukam tylko nowych meczów dla sezonu {current_season}...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) 
        context = browser.new_context()
        page = context.new_page()
        
        encrypted_email = get_setting("pzpn_email")
        encrypted_password = get_setting("pzpn_password")

        if not encrypted_email or not encrypted_password:
            print("❌ Błąd: Brak danych logowania do PZPN w bazie! Uzupełnij je w panelu ustawień.")
            browser.close()
            return
        
        pzpn_email = decrypt_data(encrypted_email)
        pzpn_password = decrypt_data(encrypted_password)

        print("🚀 Automatyczne logowanie do PZPN24...")
        page.goto("https://pzpn24.pzpn.pl/Login")
        page.fill("input#username", pzpn_email)
        page.fill("input#password", pzpn_password)
        page.click("input#kc-login")
        
        try:
            print("🍪 Sprawdzam baner cookies...")
            page.click("button[data-testid='uc-accept-all-button']", timeout=5000)
            print("🍪 Ciasteczka zaakceptowane!")
        except:
            print("🍪 Baner cookies nie wyskoczył. Lecimy dalej.")
        
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
                    print(f"    ✔️ Pomyślnie pobrano obsadę: {match['gospodarze']} vs {match['goscie']}")
                except Exception as e:
                    print(f"    ❌ Błąd dla {match['gospodarze']} vs {match['goscie']}: {e}")
            
            # Zapis wywołany po zebraniu wszystkich szczegółów!
            save_season_to_json(current_season, all_new_matches)

        print(f"\n🎉 ZAKOŃCZONO! Zabrano {len(all_new_matches)} nowych meczów.")
        browser.close()
        return all_new_matches

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