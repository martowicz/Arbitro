# Plik: api/utils.py
import sqlite3
import subprocess
import sys
from pathlib import Path

# Ważne: Wychodzimy z folderu 'api' jeden poziom wyżej (do głównego katalogu Arbitro)
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = str(BASE_DIR / "arbitro.db")

# Zamiast 'global is_syncing', używamy słownika, co jest bezpieczniejsze w rozbitych plikach
SYNC_STATE = {"is_syncing": False}

def pobierz_z_bazy(zapytanie, parametry=()):
    """Funkcja pomocnicza do wyciągania danych z bazy."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        cursor.execute(zapytanie, parametry)
        dane = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return dane
    except sqlite3.OperationalError as e:
        print(f"⚠️ Uwaga: Baza danych jest pusta lub brakuje tabeli. (Szczegóły: {e})")
        return []

def run_script(script_name: str):
    """Uruchamia dany skrypt, a po nim linkera."""
    SYNC_STATE["is_syncing"] = True
    try:
        script_path = str(BASE_DIR / script_name)
        linker_path = str(BASE_DIR / "linker.py")
        
        print(f"\n🚀 === START: {script_name} ===")
        result = subprocess.run(
            [sys.executable, script_path], 
            cwd=str(BASE_DIR),
            capture_output=True, 
            text=True
        )
        print("📝 LOGI ZE SKRYPTU:")
        print(result.stdout)
        
        if result.stderr or result.returncode != 0:
            print("❌ BŁĘDY ZE SKRYPTU (STDERR):")
            print(result.stderr)
            print("🛑 Przerywam działanie, nie odpalam linkera z powodu błędów.")
            return

        print(f"🔗 === START: linker.py ===")
        result_linker = subprocess.run(
            [sys.executable, linker_path], 
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True
        )
        print("📝 LOGI Z LINKERA:")
        print(result_linker.stdout)
        
        if result_linker.stderr:
            print("❌ BŁĘDY Z LINKERA:")
            print(result_linker.stderr)
            
        print(f"✅ === KONIEC: {script_name} ===")
        
    except Exception as e:
        print(f"❌ KRYTYCZNY BŁĄD w run_script: {e}")
    finally:
        SYNC_STATE["is_syncing"] = False