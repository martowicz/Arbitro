import sqlite3
from pathlib import Path
from db.connection import get_connection
import os
import dotenv

dotenv.load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = str(BASE_DIR / "data" / "arbitro.db")


def fetch_matches_from_db(surname_name):
    conn=get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT m.mecz_id, m.data_meczu, m.liga, m.gospodarze, m.goscie 
        FROM mecze m
        JOIN obsady o ON m.mecz_id = o.mecz_id
        JOIN sedziowie s ON o.sedzia_id = s.id
        WHERE s.imie_nazwisko = ?
    ''', (surname_name,))
    mecze = cursor.fetchall()
    conn.close()
    return mecze

def fetch_unmatched_trainings():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT aktywnosc_id, data_startu FROM treningi WHERE mecz_ID IS NULL")
    unmatched_trainings = cursor.fetchall()
    conn.close()
    return unmatched_trainings

def assign_trainings_to_matches(links_dict: dict):
    conn = get_connection()
    cursor = conn.cursor()
    data_to_update = [(m_id, t_id) for t_id, m_id in links_dict.items()]

    cursor.executemany("""
        UPDATE treningi 
        SET mecz_id = ? 
        WHERE aktywnosc_id = ?
    """, data_to_update)
    
    conn.commit()
    conn.close()


