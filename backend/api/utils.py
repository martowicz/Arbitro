import sqlite3
import subprocess
import sys
from pathlib import Path
import json

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


def extract_garmin_hr_data(file_path: str, half_number: int = None, sample_interval_sec: int = 60):
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
        return None, None
        
    ts_idx, hr_idx = None, None
    for desc in raw_data.get("metricDescriptors", []):
        if desc.get("key") == "directTimestamp": ts_idx = desc.get("metricsIndex")
        elif desc.get("key") == "directHeartRate": hr_idx = desc.get("metricsIndex")
        
    metrics_list = raw_data.get("activityDetailMetrics", [])
    if not metrics_list or ts_idx is None or hr_idx is None:
        return None, None
        
    start_ts = metrics_list[0].get("metrics", [])[ts_idx]
    if start_ts is None:
        return None, None

    labels = []
    hr_data = []
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
        
        label = format_referee_minute(mins, half_number)
        
        labels.append(label)
        hr_data.append(hr)
            
    return labels, hr_data