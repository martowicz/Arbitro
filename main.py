# Plik: main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path

# Najpierw wczytujemy .env z głównego folderu
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

# Teraz importujemy nasze rozbite moduły API
from api import match, training, coach_ai

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
app.include_router(match.router, tags=["Mecze i Kalendarz"])
app.include_router(training.router, tags=["Treningi (Garmin)"])
app.include_router(coach_ai.router, tags=["Trener AI"])

@app.get("/")
def read_root():
    return {"message": "Arbitro API działa poprawnie ze zrefaktoryzowaną strukturą!"}