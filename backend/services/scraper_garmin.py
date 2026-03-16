import os
import json

from garminconnect import Garmin
from pathlib import Path
from db.repo_garmin import load_garmin_to_db
from db.repo_settings import get_setting
from core.security import decrypt_data

BASE_DIR = Path(__file__).resolve().parent.parent

def scrape_garmin():
    print("🔐 Pobieranie i deszyfrowanie poświadczeń do Garmina z sejfu...")
    encrypted_garmin_email = get_setting("garmin_email")
    encrypted_garmin_password = get_setting("garmin_password")
    
    if not encrypted_garmin_email or not encrypted_garmin_password:
        print("🛑 Błąd: Brak danych logowania do Garmina w bazie! Uzupełnij je w panelu ustawień.")
        return

    garmin_email = decrypt_data(encrypted_garmin_email)
    garmin_password = decrypt_data(encrypted_garmin_password)
    

    try:
        print("⏳ Łączenie z serwerami Garmin Connect...")
        klient = Garmin(garmin_email, garmin_password)
        klient.login()
        print("✅ Zalogowano pomyślnie!\n")

        limit = 10
        print(f"🏃 Pobieram {limit} ostatnich aktywności...")
        
        aktywnosci = klient.get_activities(0, limit)

        folder_zapis = BASE_DIR / "data" / "training_data"
        os.makedirs(folder_zapis, exist_ok=True) 
        
        sciezka_pliku = folder_zapis / "garmin_activities.json"
        
        with open(sciezka_pliku, "w", encoding="utf-8") as f:
            json.dump(aktywnosci, f, indent=4, ensure_ascii=False)
            
        print(f"💾 Zapisano listę {len(aktywnosci)} treningów do pliku.\n")
        
        details_folder = BASE_DIR / "data" / "training_details"
        os.makedirs(details_folder, exist_ok=True)
        
        print("🔍 Sprawdzam szczegóły dla biegów i bieżni...")
        
        typy_biegowe = ["running", "treadmill_running", "indoor_running"]
        pobrane_szczegoly = 0
        
        for akt in aktywnosci:
            typ = akt.get("activityType", {}).get("typeKey", "unknown")
            aktywnosc_id = str(akt.get("activityId"))
            
            if typ in typy_biegowe and aktywnosc_id and aktywnosc_id != "None":
                sciezka_detali = details_folder / f"{aktywnosc_id}.json"
                
                if not os.path.exists(sciezka_detali):
                    print(f"   📥 Pobieram wykresy tętna/tempa dla: {akt.get('activityName')} ({aktywnosc_id})")
                    try:
                        szczegoly = klient.get_activity_details(aktywnosc_id)
                        with open(sciezka_detali, "w", encoding="utf-8") as f:
                            json.dump(szczegoly, f, indent=4, ensure_ascii=False)
                        pobrane_szczegoly += 1
                    except Exception as e:
                        print(f"   ⚠️ Błąd pobierania szczegółów dla {aktywnosc_id}: {e}")
                
        print(f"📈 Zapisano {pobrane_szczegoly} nowych plików ze szczegółami treningów.\n")
        print("-" * 50)

        # Bezpośrednie wywołanie zapisu do bazy
        load_garmin_to_db()

    except Exception as e:
        print(f"\n❌ Wystąpił błąd podczas pobierania danych z Garmina:\n{e}")

if __name__ == "__main__":
    scrape_garmin()