import sqlite3
import subprocess
import sys
from pathlib import Path

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