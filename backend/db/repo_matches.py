from .connection import get_connection, create_all_tables

def get_referee_id(cursor, full_name):
    """Pobiera ID sędziego z bazy lub tworzy nowe, jeśli go nie ma."""
    cursor.execute('INSERT OR IGNORE INTO sedziowie (imie_nazwisko) VALUES (?)', (full_name,))
    cursor.execute('SELECT id FROM sedziowie WHERE imie_nazwisko = ?', (full_name,))
    return cursor.fetchone()[0]

def load_known_data():
    """Wciąga z bazy to, co już znamy (ID oraz sygnatury)."""
    known_ids = set()
    known_signatures = set()
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT LOWER(mecz_id), data_meczu, gospodarze, goscie FROM mecze")
        for row in cursor.fetchall():
            if row[0]: known_ids.add(row[0])
            signature = f"{str(row[1]).lower()}_{str(row[2]).lower()}_{str(row[3]).lower()}"
            known_signatures.add(signature)
        conn.close()
    except Exception:
        # Jeśli bazy jeszcze nie ma, po prostu omijamy
        pass
        
    return known_ids, known_signatures

def save_matches_to_db(matches):
    """Bierze pobrane mecze (z RAM-u) i wrzuca je bezpiecznie do SQLite."""
    if not matches:
        return

    create_all_tables()
    conn = get_connection()
    cursor = conn.cursor()

    match_counter = 0
    for match in matches:
        url = match.get('szczegoly_url', '')
        match_id = url.split('meczId=')[-1].lower() if 'meczId=' in url else None
        
        if not match_id:
            continue

        cursor.execute('''
        INSERT OR IGNORE INTO mecze 
        (mecz_id, sezon, runda, liga, kolejka, data_meczu, gospodarze, goscie, wynik)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            match_id, match.get('sezon'), match.get('runda'), match.get('liga'),
            match.get('kolejka'), match.get('data'), match.get('gospodarze'),
            match.get('goscie'), match.get('wynik')
        ))

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
    print(f"✅ Zapisano {match_counter} nowych meczów prosto do bazy.")