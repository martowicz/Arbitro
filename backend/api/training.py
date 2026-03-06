# Plik: api/training.py
from fastapi import APIRouter, BackgroundTasks
from .utils import run_script

router = APIRouter(prefix="/api")

@router.post("/sync/garmin")
def sync_garmin(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_script, "scraper_garmin.py")
    return {"status": "started", "message": "Synchronizacja Garmin ruszyła w tle."}