from fastapi import APIRouter, HTTPException
from .utils import fetch_from_db, process_activities_to_charts, generate_training_summary_prompt, extract_garmin_data
from openai import OpenAI
from pathlib import Path

router = APIRouter(prefix="/api", tags=["Charts"])
client = OpenAI()

BASE_DIR = Path(__file__).resolve().parent.parent

@router.get("/matches/{mecz_id}/chart_data")
def get_match_chart_data(mecz_id: str):
    query = "SELECT aktywnosc_id FROM treningi WHERE mecz_id = ? ORDER BY data_startu ASC"
    results = fetch_from_db(query, (mecz_id,))
    #results should be two training sessions - from first half and second half
    if not results: 
        raise HTTPException(404, "Brak przypisanych połów z Garmina.")
    
    tasks = [(row['aktywnosc_id'], f"Połowa {idx+1}", idx+1) for idx, row in enumerate(results)]
    
    return process_activities_to_charts(tasks)


@router.get("/trainings/{aktywnosc_id}/chart_data")
def get_training_chart_data(aktywnosc_id: str):
    #one training session to built a chart for
    tasks = [(aktywnosc_id, "Dane treningu", None)]
    
    return process_activities_to_charts(tasks)

@router.get("/analysis/{item_type}/{item_id}")
def get_ai_analysis(item_type: str, item_id: str):
    activities_to_analyze = []
    
    # 1. Zbieramy ID aktywności (jedna dla treningu, dwie dla meczu)
    if item_type == "match":
        query = "SELECT aktywnosc_id FROM treningi WHERE mecz_id = ? ORDER BY data_startu ASC"
        results = fetch_from_db(query, (item_id,))
        if not results: raise HTTPException(404, "Brak danych")
        activities_to_analyze = [row['aktywnosc_id'] for row in results]
    else:
        activities_to_analyze = [item_id]

    # 2. Sklejamy dane ze wszystkich plików
    all_hr = []
    all_speed = []
    sample_interval = 10 # Musi być taki sam jak dla wykresów!
    
    for act_id in activities_to_analyze:
        file_path = BASE_DIR / "data" / "training_details" / f"{act_id}.json"
        if file_path.exists():
            _, hr, speed = extract_garmin_data(file_path, half_number=None, sample_interval_sec=sample_interval)
            if hr: all_hr.extend(hr)
            if speed: all_speed.extend(speed)
            
    if not all_hr:
        raise HTTPException(404, "Brak danych do analizy.")

    # 3. Kompresja danych do Promptu (używamy funkcji z utils.py!)
    prompt = generate_training_summary_prompt(all_hr, all_speed, sample_interval)

    # 4. Pytamy OpenAI
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # Polecam gpt-4o-mini jeśli masz dostęp, jest świetny i tani
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=250
        )
        ai_message = response.choices[0].message.content
        return {"summary": ai_message}
    except Exception as e:
        print("Błąd OpenAI:", e)
        raise HTTPException(500, "Nie udało się wygenerować analizy AI.")