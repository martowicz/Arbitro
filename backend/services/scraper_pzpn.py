import os
import json
import time
from playwright.sync_api import sync_playwright
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor


from db.repo_matches import load_known_data, save_matches_to_db
from db.repo_settings import get_setting
from core.security import decrypt_data

BASE_DIR = Path(__file__).resolve().parent.parent
CURRENT_SEASON = "2025/2026"
SESSION_FILE = BASE_DIR / "data" / ".pzpn_session.json"


def ensure_logged_in(page):
    if "login" in page.url or "authenticate" in page.url:
        print("❌ SESJA PADŁA - wróciłeś do logowania")
        return False
    return True

def save_season_to_json(season, new_matches):
    """Zapisuje dane do pliku JSON w folderze match_data."""
    if not new_matches: return
    
    target_folder = BASE_DIR / "data" / "match_data"
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

def fetch_single_match_details(match):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        context = browser.new_context(storage_state=str(SESSION_FILE))
        page = context.new_page()
        
        try:
            page.goto(match["szczegoly_url"])
            page.wait_for_load_state("networkidle")

            page.evaluate("""
            const removeRODO = () => {
                const shadowHost = document.getElementById('usercentrics-root');
                if (shadowHost) shadowHost.remove();
                const overlays = document.querySelectorAll('.uc-overlay, .uc-container');
                overlays.forEach(el => el.remove());
                document.body.style.overflow = 'auto';
            };
            removeRODO();
            """)
            
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
            print(f"    ✔️ [Wątek] Pomyślnie pobrano obsadę: {match['gospodarze']} vs {match['goscie']}")
        except Exception as e:
            print(f"    ❌ [Wątek] Błąd dla {match['gospodarze']} vs {match['goscie']}: {e}")
        finally:
            browser.close()
            
    return match

def scrape_arbitro(current_season, is_new_user, known_ids=None, known_signatures=None):
    known_ids = known_ids or set()
    known_signatures = known_signatures or set()
    all_new_matches = []

    if is_new_user: print(f"🆕 WYKRYTO NOWEGO UŻYTKOWNIKA. Rozpoczynam pełne pobieranie dla sezonu {current_season}...")
    else: print(f"🔄 ZNANY UŻYTKOWNIK. Szukam tylko nowych meczów dla sezonu {current_season}...")


    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            java_script_enabled=True,
            locale="pl-PL",
            timezone_id="Europe/Warsaw"
        )
        page = context.new_page()
        
        encrypted_email = get_setting("pzpn_email")
        encrypted_password = get_setting("pzpn_password")

        if not encrypted_email or not encrypted_password:
            print("❌ Błąd: Brak danych logowania do PZPN w bazie! Uzupełnij je w panelu ustawień.")
            browser.close()
            return []
        
        pzpn_email = decrypt_data(encrypted_email)
        pzpn_password = decrypt_data(encrypted_password)

        print("🚀 Automatyczne logowanie do PZPN24...")
        page.goto("https://pzpn24.pzpn.pl/Login")
        time.sleep(2)
        page.fill("input#username", pzpn_email)
        time.sleep(1)
        page.fill("input#password", pzpn_password)
        time.sleep(1)
        page.click("input#kc-login")
        page.wait_for_load_state("load")
        time.sleep(3)

        print("🛡️ Neutralizuję baner RODO...")
        page.evaluate("""
            const shadowHost = document.getElementById('usercentrics-root');
            if (shadowHost) shadowHost.remove();
            document.body.style.overflow = 'auto';
        """)
        

        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

        if not ensure_logged_in(page):
            print("❌ Logowanie NIE powiodło się poprawnie")
            browser.close()
            return []
            
        print("✅ Logowanie zakończone (zweryfikowane).")

        print("💾 Zapisuję sesję do pliku...")
        SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        context.storage_state(path=str(SESSION_FILE))
        print(f"✅ Plik sesji zapisany pod: {SESSION_FILE}")
        
        current_profile_text = page.locator(".navbar-right .dropdown-toggle").first.inner_text().upper()
        
        if "SĘDZIA" not in current_profile_text:
            print("🔄 Jesteśmy na Profilu Podstawowym. Przełączam na konto Sędziego...")
            
            page.locator(".navbar-right .dropdown-toggle").first.click()
            page.wait_for_timeout(1000)
            
            referee_link = page.locator("a[href*='ZmienKonto']", has_text="Sędzia").first
            
            if referee_link.count() > 0:
                referee_link.click()
                print("✅ Kliknięto zmianę konta na Sędzia.")
                page.wait_for_load_state("networkidle")
                time.sleep(2)
            else:
                print("⚠️ Nie znaleziono linku do konta sędziego w menu!")

        
        page.evaluate('document.getElementById("usercentrics-root")?.remove()')


        page.screenshot(path="debug_before_click.png", full_page=True)
        print(page.url)
        print(page.title())
        print(page.content()[:5000]) 
        print("\n🔗 LISTA LINKÓW:")
        links = page.locator("a")


        print("\n🔎 SZUKAM LINKU DO OBSADY...")

        obsady_link = page.locator("a[href*='Obsady']").first

        if obsady_link.count() == 0:
            print("❌ NIE ZNALEZIONO linku do Obsady")
            browser.close()
            return []

        page.goto("https://pzpn24.pzpn.pl/Ogolne/Obsady")
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
                
                page.evaluate('document.getElementById("usercentrics-root")?.remove()')

                next_btn = page.locator("#spotkania_tabela_next")
                if next_btn.is_visible() and "disabled" not in (next_btn.get_attribute("class") or ""):
                    next_btn.click(force=True) 
                    time.sleep(1.5)
                    continue
                break

        browser.close()

    
    # Mutlithreading
    
    if not all_new_matches:
        print(f"  ✅ Brak nowych meczów w sezonie {current_season}.")
        if SESSION_FILE.exists(): SESSION_FILE.unlink()
        return []

    print(f"\n⚡ Odpalam {min(4, len(all_new_matches))} wątków do pobrania szczegółów {len(all_new_matches)} meczów...")
    
    final_matches = []
    try:
        with ThreadPoolExecutor(max_workers=4) as executor:
            results = executor.map(fetch_single_match_details, all_new_matches)
            final_matches = list(results)
    finally:
        if SESSION_FILE.exists():
            SESSION_FILE.unlink()
            print("🧹 Wyczyszczono pliki sesyjne.")

    save_season_to_json(current_season, final_matches)

    print(f"\n🎉 ZAKOŃCZONO! Zabrano {len(final_matches)} nowych meczów.")
    return final_matches

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
        for m in new_matches[:3]:
            print(f"DEBUG: Mecz {m['gospodarze']} ma obsadę: {m.get('obsada')}")
        save_matches_to_db(new_matches)
    else:
        print("👍 Wszystko jest aktualne, brak nowych meczów do dodania do bazy.")

if __name__ == "__main__":
    run_scraper()