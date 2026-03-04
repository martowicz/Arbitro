import sqlite3
import dotenv
import os
from datetime import datetime, timedelta
from pathlib import Path

dotenv.load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = str(BASE_DIR / "arbitro.db")
MOJE_NAZWISKO = os.getenv("MOJE_NAZWISKO")
GARMIN_JSON = str(BASE_DIR / "training_data" / "garmin_activities.json")

# ==========================================
# 1. DEFINICJE KLAS (Twoje obiekty)
# ==========================================
class PZPNMatch:
    def __init__(self, mecz_id, data_meczu, gospodarze, goscie, liga, rola):
        self.mecz_id = mecz_id
        # Poprawiona podwójna przypisanie
        self.data_meczu_dt = datetime.strptime(data_meczu, "%Y-%m-%d %H:%M")
        self.gospodarze = gospodarze
        self.goscie = goscie
        self.liga = liga
        self.rola = rola
        self.first_half_training = None  
        self.second_half_training = None
        self.average_heart_rate = None
        self.full_distance = 0.0  
        self.full_calories = 0  
        
    def set_training_for_half(self, training_obj, half):
        if half == "first":
            self.first_half_training = training_obj
        elif half == "second":
            self.second_half_training = training_obj

    def set_stats(self):
        if self.first_half_training and self.second_half_training:
            # Ustawiamy średnie tętno z obu połówek
            avg_hr = (self.first_half_training.tetno_sr * self.first_half_training.czas_min + self.second_half_training.tetno_sr * self.second_half_training.czas_min) / (self.first_half_training.czas_min + self.second_half_training.czas_min)
            self.average_heart_rate = int(avg_hr)
            
            # Sumujemy dystansy obu połówek
            self.full_distance = self.first_half_training.dystans_km + self.second_half_training.dystans_km
            self.full_calories = self.first_half_training.kalorie + self.second_half_training.kalorie

    def print_stats(self):
        print(f"⚽ {self.liga}: {self.gospodarze} vs {self.goscie} ({self.data_meczu_dt.strftime('%Y-%m-%d %H:%M')})")
        if self.first_half_training:
            print(f"   ┣━ 1. Połowa: {self.first_half_training.dystans_km} km, ⌚ {self.first_half_training.czas_min} min, ❤️ {self.first_half_training.tetno_sr} bpm, 🔥 {self.first_half_training.kalorie} kcal")
        else:
            print("   ┣━ 1. Połowa: Brak zapisu z Garmina!")
        if self.second_half_training:
            print(f"   ┗━ 2. Połowa: {self.second_half_training.dystans_km} km, ⌚ {self.second_half_training.czas_min} min, ❤️ {self.second_half_training.tetno_sr} bpm, 🔥 {self.second_half_training.kalorie} kcal")
        else:
            print("   ┗━ 2. Połowa: Brak zapisu z Garmina!")
        if self.average_heart_rate:
            print(f"   ➤ Średnie tętno z meczu: ❤️ {self.average_heart_rate} bpm")
        if self.full_distance > 0:
            print(f"   ➤ Całkowity dystans z meczu: 🏃‍♂️ {round(self.full_distance, 2)} km")
        if self.full_calories > 0:
            print(f"   ➤ Całkowite kalorie z meczu: 🔥 {self.full_calories} kcal")

class GarminTraining:
    def __init__(self, aktywnosc_id, typ, nazwa, data_startu, dystans_km, czas_min, tetno_sr, kalorie, mecz_ID=None):
        self.aktywnosc_id = aktywnosc_id
        self.typ = typ
        self.nazwa = nazwa
        self.data_startu_dt = datetime.strptime(data_startu, "%Y-%m-%d %H:%M:%S")
        self.dystans_km = dystans_km
        self.czas_min = czas_min
        self.tetno_sr = tetno_sr
        self.kalorie = kalorie
        self.mecz_id = mecz_ID

# ==========================================
# 2. POBIERANIE Z BAZY I TWORZENIE OBIEKTÓW
# ==========================================
def load_objects_from_database():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Wyciągamy Twoje mecze
    cursor.execute('''
        SELECT m.mecz_id, m.data_meczu, m.gospodarze, m.goscie, m.liga, o.rola 
        FROM mecze m
        JOIN obsady o ON m.mecz_id = o.mecz_id
        JOIN sedziowie s ON o.sedzia_id = s.id
        WHERE s.imie_nazwisko = ?
    ''', (MOJE_NAZWISKO,))
    
    matches_objects = [PZPNMatch(**dict(row)) for row in cursor.fetchall()]

    # Wyciągamy WSZYSTKIE treningi (interesują nas tylko te biegowe/chodzone)
    cursor.execute("SELECT * FROM treningi WHERE typ IN ('running')")
    trainings_objects = [GarminTraining(**dict(row)) for row in cursor.fetchall()]

    conn.close()
    return matches_objects, trainings_objects

# ==========================================
# 3. LOGIKA ŁĄCZENIA (PREPROCESSING)
# ==========================================
def link_matches_to_trainings(matches, trainings):
    print("🔄 Rozpoczynam inteligentne łączenie połówek meczów z Garminem...\n")
    connected_matches = 0

    for match in matches:
        if not match.data_meczu_dt:
            continue
            
        # Krok A: Szukamy treningów z tego samego dnia (Data bez godziny)
        trainings_from_matchday = [
            t for t in trainings 
            if t.data_startu_dt and t.data_startu_dt.date() == match.data_meczu_dt.date()
        ]

        if not trainings_from_matchday:
            continue # Brak treningów w dniu meczu

        # Krok B: Sortujemy te treningi chronologicznie (od najwcześniejszego)
        trainings_from_matchday.sort(key=lambda t: t.data_startu_dt)

        matching_halves = []

        # Krok C: Filtrujemy czasowo. Mecz trwa ok. 2 godzin (z przerwą).
        # Szukamy aktywności, które zaczęły się od 15 min przed meczem do 120 min po rozpoczęciu.
        for trening in trainings_from_matchday:
            time_difference = trening.data_startu_dt - match.data_meczu_dt
            time_difference_minutes = time_difference.total_seconds() / 60.0

            if -15 <= time_difference_minutes <= 120:
                matching_halves.append(trening)

        # Krok D: Przypisujemy do połówek na podstawie kolejności
        if len(matching_halves) > 0:
            # Pierwsza znaleziona aktywność w tym oknie czasowym to 1. połowa
            match.set_training_for_half(matching_halves[0], "first")
            connected_matches += 1
            
            if len(matching_halves) > 1:
                # Druga aktywność to 2. połowa
                match.set_training_for_half(matching_halves[1], "second")
                
            # --- Opcjonalny wydruk dla podglądu ---
            print(f"⚽ {match.liga}: {match.gospodarze} vs {match.goscie} ({match.data_meczu_dt.strftime('%Y-%m-%d %H:%M')})")
            print(f"   ┣━ 1. Połowa: {match.first_half_training.dystans_km} km (⌚ {match.first_half_training.data_startu_dt.strftime('%Y-%m-%d %H:%M')})")
            if match.second_half_training:
                print(f"   ┗━ 2. Połowa: {match.second_half_training.dystans_km} km (⌚ {match.second_half_training.data_startu_dt.strftime('%Y-%m-%d %H:%M')})")
            else:
                print("   ┗━ 2. Połowa: Brak zapisu z Garmina!")
            print("-" * 50)

    print(f"✅ Zakończono! Zlinkowano {connected_matches} meczów z aktywnościami Garmina.")
    for match in matches:
        match.set_stats()
        # Możesz odkomentować poniższą linię, jeśli chcesz widzieć pełne podsumowanie po połączeniu
        # match.print_stats()
        
    save_linked_matches_to_db(matches)  # Zapisujemy powiązania do bazy

# ==========================================
# 4. ZAPIS PRZETWORZONYCH OBIEKTÓW DO BAZY
# ==========================================
def save_linked_matches_to_db(linked_matches):
    """Pobiera zlinkowane obiekty PZPNMatch i przypisuje mecz_id do tabeli treningi."""
    print("\n💾 Zapisuję powiązania (mecz_id) do tabeli 'treningi'...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    saved_count = 0
    for match in linked_matches:
        updated_any = False
        
        # Jeśli istnieje pierwsza połowa, dopisz jej ID meczu
        if match.first_half_training:
            cursor.execute("""
                UPDATE treningi 
                SET mecz_id = ? 
                WHERE aktywnosc_id = ?
            """, (match.mecz_id, match.first_half_training.aktywnosc_id))
            updated_any = True
            
        # Jeśli istnieje druga połowa, dopisz jej ID meczu
        if match.second_half_training:
            cursor.execute("""
                UPDATE treningi 
                SET mecz_id = ? 
                WHERE aktywnosc_id = ?
            """, (match.mecz_id, match.second_half_training.aktywnosc_id))
            updated_any = True

        if updated_any:
            saved_count += 1

    conn.commit()
    conn.close()
    print(f"✅ Sukces! Zaktualizowano powiązania dla {saved_count} meczów w tabeli Garmina.")

# ==========================================
# 5. START SYSTEMU
# ==========================================
if __name__ == "__main__":
    print("🚀 Uruchamiam system łączenia danych z PZPN i Garmina...\n")
    matches, trainings = load_objects_from_database()
    link_matches_to_trainings(matches, trainings)