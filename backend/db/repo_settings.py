from .connection import get_connection

def save_setting(klucz: str, wartosc: str):
    """Zapisuje dowolne ustawienie w bazie (np. zaszyfrowane hasło)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO ustawienia (klucz, wartosc) VALUES (?, ?)', (klucz, wartosc))
    conn.commit()
    conn.close()

def get_setting(klucz: str) -> str:
    """Pobiera ustawienie z bazy. Zwraca pusty string, jeśli klucz nie istnieje."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT wartosc FROM ustawienia WHERE klucz = ?', (klucz,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else ""
    except Exception:
        # Tabela może jeszcze nie istnieć przy pierwszym uruchomieniu
        return ""