# Plik: api/coach_ai.py
import os
import sqlite3
from datetime import datetime, timedelta
from fastapi import APIRouter
from openai import OpenAI
from .utils import fetch_from_db, DB_PATH, BASE_DIR

router = APIRouter(prefix="/api", tags=["Coach AI"])

@router.get("/trener_ai")
def ask_ai():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "Brak klucza API dla OpenAI."}
    
    client = OpenAI(api_key=api_key)
    dzis_obj = datetime.now()
    today = dzis_obj.strftime("%Y-%m-%d")
    data_graniczna = (dzis_obj - timedelta(days=7)).strftime('%Y-%m-%d')
    MOJE_NAZWISKO = os.getenv("MOJE_NAZWISKO", "Martowicz Jan")
    
    dni_tygodnia_pl = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
    dzisiaj_dzien_pl = dni_tygodnia_pl[dzis_obj.weekday()]
    
    kalendarz_pomocniczy = "ŚCIĄGAWKA KALENDARZOWA NA NAJBLIŻSZE DNI:\n"
    for i in range(7):
        data_krok = dzis_obj + timedelta(days=i)
        kalendarz_pomocniczy += f"- {data_krok.strftime('%Y-%m-%d')} to {dni_tygodnia_pl[data_krok.weekday()]}\n"
        
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT m.data_meczu, m.gospodarze, m.goscie, o.rola, SUM(t.dystans_km) as full_distance, ROUND(AVG(t.tetno_sr)) as average_heart_rate
            FROM mecze m
            JOIN obsady o ON m.mecz_id = o.mecz_id JOIN sedziowie s ON o.sedzia_id = s.id
            LEFT JOIN treningi t ON m.mecz_id = t.mecz_id
            WHERE s.imie_nazwisko = ? AND m.data_meczu >= ?
            GROUP BY m.mecz_id ORDER BY m.data_meczu ASC
        ''', (MOJE_NAZWISKO, data_graniczna))
        mecze = cursor.fetchall()
        
        cursor.execute('SELECT data_startu, nazwa, dystans_km, tetno_sr FROM treningi WHERE data_startu >= ? AND mecz_id IS NULL ORDER BY data_startu DESC', (data_graniczna,))
        inne_treningi = cursor.fetchall()
        conn.close()
    except Exception as e:
        return {"porada": f"Błąd bazy: {e}"}
    
    przeszle_mecze = [m for m in mecze if m['data_meczu'] and m['data_meczu'][:10] <= today]
    przyszle_mecze = [m for m in mecze if m['data_meczu'] and m['data_meczu'][:10] > today]

    kontekst = f"UWAGA: Dzisiejsza data to {today} ({dzisiaj_dzien_pl}).\n\n{kalendarz_pomocniczy}\nOto moje obciążenie fizyczne:\n\n⚽ ZREALIZOWANE MECZE:\n"
    for m in przeszle_mecze:
        kontekst += f"- {m['data_meczu']}: {m['rola']} ({m['gospodarze']} vs {m['goscie']}) | {m['full_distance'] or 0} km | Śr. tętno: {m['average_heart_rate'] or 'Brak'} bpm\n"
    if not przeszle_mecze: kontekst += "- Brak meczów.\n"
        
    kontekst += "\n🏃‍♂️ INNE ZREALIZOWANE TRENINGI:\n"
    for t in inne_treningi:
        kontekst += f"- {t['data_startu']}: {t['nazwa']} | {t['dystans_km']} km | Śr. tętno: {t['tetno_sr']} bpm\n"
    if not inne_treningi: kontekst += "- Brak dodatkowych treningów.\n"

    kontekst += "\n📅 ZAPLANOWANE MECZE:\n"
    for m in przyszle_mecze:
        kontekst += f"- {m['data_meczu']}: {m['rola']} ({m['gospodarze']} vs {m['goscie']})\n"
    if not przyszle_mecze: kontekst += "- Brak zaplanowanych meczów.\n"

    try:
        with open(BASE_DIR / "prompt_ai.txt", "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except: return {"porada": "Błąd: Nie znaleziono pliku prompt_ai.txt!"}

    try:
        response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": kontekst}])
        return {"porada": response.choices[0].message.content}
    except Exception as e:
        return {"porada": f"Błąd OpenAI: {str(e)}"}