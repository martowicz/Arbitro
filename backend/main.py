# Plik: main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
import os
print(f"DEBUG: Szukam bazy w: {os.path.abspath('arbitro.db')}")
print(f"DEBUG: Czy plik istnieje? {os.path.exists('arbitro.db')}")

# Najpierw wczytujemy .env z głównego folderu
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

# Teraz importujemy nasze rozbite moduły API
from api import events, sync, coach_ai

app = FastAPI(title="Arbitro API")

# Zabezpieczenie CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rejestrujemy moduły w aplikacji (Routery z "api/" folderu)


app.include_router(events.router)
app.include_router(sync.router)
#app.include_router(coach_ai.router)

@app.get("/")
def read_root():
    return {"message": "Arbitro API działa poprawnie ze zrefaktoryzowaną strukturą!"}