import sqlite3
import subprocess
import sys
from pathlib import Path
import json
from fastapi import HTTPException

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = str(BASE_DIR / "arbitro.db")

# Global sync state
SYNC_STATE = {"is_syncing": False}

def fetch_from_db(query: str, params: tuple = ()):
    """Helper function to fetch data from SQLite database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        cursor.execute(query, params)
        data = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return data
    except sqlite3.OperationalError as e:
        print(f"⚠️ Warning: Database error or missing table. (Details: {e})")
        return []

def run_sync_process(scripts_to_run: list[str]):
    """
    Uniwersalna funkcja do synchronizacji. Przyjmuje listę skryptów (np. sam PZPN, 
    sam Garmin, albo oba naraz), uruchamia je po kolei, a na koniec zawsze odpal linkera.
    """
    SYNC_STATE["is_syncing"] = True
    try:
        print(f"\n🚀 === START SYNCHRONIZACJI: {', '.join(scripts_to_run)} ===")
        
        # 1. Uruchamiamy wszystkie skrypty z listy po kolei
        for script_name in scripts_to_run:
            script_path = str(BASE_DIR / script_name)
            print(f"⏳ Uruchamiam: {script_name}...")
            
            result = subprocess.run([sys.executable, script_path], cwd=str(BASE_DIR), capture_output=True, text=True)
            print(f"📝 LOGI ({script_name}):\n{result.stdout.strip()}")
            
            # Jeśli którykolwiek skrypt wywali błąd, przerywamy cały proces
            if result.stderr or result.returncode != 0:
                print(f"❌ BŁĘDY ({script_name}):\n{result.stderr.strip()}")
                print("🛑 Przerywam proces. Linker nie zostanie uruchomiony.")
                return 

        # 2. Jeśli wszystkie skrypty przeszły bezbłędnie, odpalamy Linkera
        linker_path = str(BASE_DIR / "linker.py")
        print(f"🔗 === START: linker.py ===")
        
        result_linker = subprocess.run([sys.executable, linker_path], cwd=str(BASE_DIR), capture_output=True, text=True)
        print(f"📝 LOGI (linker.py):\n{result_linker.stdout.strip()}")
        
        if result_linker.stderr:
            print(f"❌ BŁĘDY (linker.py):\n{result_linker.stderr.strip()}")
            
        print(f"✅ === KONIEC SYNCHRONIZACJI ===")
        
    except Exception as e:
        print(f"❌ KRYTYCZNY BŁĄD w run_sync_process: {e}")
    finally:
        SYNC_STATE["is_syncing"] = False

def format_time(time_in_minutes: float) -> str:
    """Converts minutes to H:MM format (e.g., 65 -> 1:05)."""
    if not time_in_minutes or time_in_minutes < 3:
        return "0:00"
    
    hours = int(time_in_minutes // 60)
    minutes = int(time_in_minutes % 60)
    # :02d gwarantuje, że zawsze będą dwie cyfry (np. 05 zamiast 5)
    return f"{hours}:{minutes:02d}"


def format_referee_minute(mins: int, half_number: int = None) -> str:
    """Formatuje minuty na czas sędziowski (np. 45+2)."""
    if half_number == 1:
        return f"45+{mins - 45 + 1}" if mins >= 45 else str(mins + 1)
    elif half_number == 2:
        total_mins = 45 + mins
        return f"90+{total_mins - 90 + 1}" if total_mins >= 90 else str(total_mins + 1)
    
    return str(mins + 1)


def extract_garmin_data(file_path: str, half_number: int = None, sample_interval_sec: int = 60):
    """
    Wyciąga i próbkkuje dane tętna z pliku Garmina.
    
    :param file_path: Ścieżka do pliku JSON
    :param half_number: 1 dla pierwszej połowy, 2 dla drugiej, None dla treningów
    :param sample_interval_sec: Co ile sekund pobierać próbkę (domyślnie 60s)
    :return: Krotka (labels, hr_data)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except Exception:
        return None, None, None
        
    ts_idx, hr_idx, speed_idx = None, None, None
    for desc in raw_data.get("metricDescriptors", []):
        if desc.get("key") == "directTimestamp": ts_idx = desc.get("metricsIndex")
        elif desc.get("key") == "directHeartRate": hr_idx = desc.get("metricsIndex")
        elif desc.get("key") == "directSpeed": speed_idx = desc.get("metricsIndex")
        
    metrics_list = raw_data.get("activityDetailMetrics", [])
    if not metrics_list or ts_idx is None or hr_idx is None:
        return None, None, None
        
    start_ts = metrics_list[0].get("metrics", [])[ts_idx]
    if start_ts is None:
        return None, None, None

    labels = []
    hr_data = []
    speed_data = []
    last_sampled_ts = None
    
    for sample in metrics_list:
        m = sample.get("metrics", [])
        if len(m) <= max(ts_idx, hr_idx): continue
        
        curr_ts = m[ts_idx]
        hr = m[hr_idx]
        
        if curr_ts is None or hr is None or hr == 0: continue
        
        # LOGIKA PRÓBKOWANIA: Sprawdzamy, czy minęło wystarczająco dużo czasu (w milisekundach)
        if last_sampled_ts is not None:
            if (curr_ts - last_sampled_ts) < (sample_interval_sec * 1000):
                continue # Pomijamy tę próbkę, bo jest za wcześnie
                
        last_sampled_ts = curr_ts
        mins = int((curr_ts - start_ts) / 60000)

        raw_speed = m[speed_idx] if speed_idx is not None and len(m) > speed_idx and m[speed_idx] is not None else 0
        speed_kmh = round(raw_speed * 3.6, 1) # Mnożnik 0.1 z Garmina * 3.6 do km/h
        
        label = format_referee_minute(mins, half_number)
        
        labels.append(label)
        hr_data.append(hr)
        speed_data.append(speed_kmh)
            
    return labels, hr_data, speed_data


def build_chart_dataset(title: str, labels: list, hr_data: list, speed_data: list) -> dict:
    """Buduje gotowy słownik z danymi i wyglądem wykresu dla Chart.js"""
    return {
        "title": title, 
        "chart": {
            "labels": labels,
            "datasets": [
                {
                    "label": "Tętno (bpm)",
                    "data": hr_data,
                    "borderColor": "#e74c3c",
                    "backgroundColor": "rgba(231, 76, 60, 0.2)",
                    "fill": True,
                    "yAxisID": "heart_rate",
                    "tension": 0.4,
                    "pointRadius": 1
                },
                {
                    "label": "Prędkość (km/h)",
                    "data": speed_data,
                    "borderColor": "#3498db",
                    "backgroundColor": "transparent",
                    "fill": True,
                    "yAxisID": "speed",
                    "tension": 0.4,
                    "pointRadius": 1
                }
            ]
        }
    }

def process_activities_to_charts(activities_info: list) -> list:
    """
    Uniwersalna funkcja generująca listę wykresów.
    Przyjmuje listę krotek: (aktywnosc_id, tytul_wykresu, numer_polowy)
    """
    charts = []
    for act_id, title, half_num in activities_info:
        file_path = BASE_DIR / "training_details" / f"{act_id}.json"
        
        if file_path.exists():
            labels, hr, speed = extract_garmin_data(file_path, half_number=half_num, sample_interval_sec=10)
            if labels and hr:
                charts.append(build_chart_dataset(title, labels, hr, speed))
                
    if not charts:
        raise HTTPException(404, "Pliki nie istnieją lub nie zawierają danych o tętnie.")
        
    return charts


# Dodaj to na dole pliku utils.py

def generate_training_summary_prompt(hr_data: list, speed_data: list, sample_interval_sec: int) -> str:
    """Kompresuje surowe dane do tekstowej pigułki dla OpenAI. - 5 minute chunks"""
    if not hr_data:
        return "Brak danych."

    total_points = len(hr_data)
    duration_mins = (total_points * sample_interval_sec) / 60

    avg_hr = int(sum(hr_data) / total_points)
    max_hr = max(hr_data)
    max_speed = max(speed_data) if speed_data else 0

    # Liczymy sprinty (zrywy powyżej 24 km/h)
    sprints_count = sum(1 for s in speed_data if s >= 24)

    # Dzielimy na 10-minutowe bloki
    points_per_5_min = int((5 * 60) / sample_interval_sec)
    chunks_text = ""

    for i in range(0, total_points, points_per_5_min):
        chunk_hr = hr_data[i:i + points_per_5_min]
        chunk_speed = speed_data[i:i + points_per_5_min]

        start_min = int((i * sample_interval_sec) / 60)
        end_min = int(((i + len(chunk_hr)) * sample_interval_sec) / 60)

        c_avg_hr = int(sum(chunk_hr) / len(chunk_hr))
        c_max_speed = max(chunk_speed) if chunk_speed else 0

        chunks_text += f"- Minuty {start_min}-{end_min}: Średnie HR: {c_avg_hr} bpm, Max Prędkość: {c_max_speed} km/h\n"

    # Budujemy finalny prompt
        prompt = f"""Jako profesjonalny trener przygotowania motorycznego sędziów piłkarskich, przeanalizuj poniższe dane wydolnościowe.

        DANE WEJŚCIOWE:
        - Czas trwania: ~{int(duration_mins)} minut
        - Średnie tętno: {avg_hr} bpm
        - Maksymalne tętno: {max_hr} bpm
        - Maksymalna prędkość: {max_speed} km/h
        - Liczba zrywów/sprintów (>24 km/h): {sprints_count}

        PRZEBIEG W BLOKACH 10-MINUTOWYCH:
        {chunks_text}

        TWOJE ZADANIE:
        Napisz zwięzłą, wysoce merytoryczną i motywującą analizę (maksymalnie 4-5 zdań).
        Rozpoznaj typ treningu na bazie zmian tętna prędkości.
        Jeśli czas całkowity to około 90 min lub więcej, to aktywność ta to mecz, jeśli mniej, oznacza trening. 
        Zamiast po prostu czytać liczby, wyciągnij z nich wnioski trenera:
        1. Zidentyfikuj główne trendy (np. relacja tętna do prędkości w czasie).
        2. Wskaż ewentualne anomalie (niezwykłe skoki intensywności, momenty kryzysowe, nagłe spadki formy).
        3. Oceń ogólną dyspozycję fizyczną na tle całego wysiłku.

        Opieraj się wyłącznie na dostarczonych statystykach. Zwracaj się bezpośrednio do sędziego (na "Ty") z pozycji wspierającego, ale wymagającego eksperta.
        """
    return prompt