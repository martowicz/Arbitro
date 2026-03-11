from fastapi import APIRouter, BackgroundTasks
from .utils import run_sync_process, SYNC_STATE

router = APIRouter(prefix="/api/sync", tags=["Synchronization"])

@router.get("/status")
def get_sync_status():
    return {"is_syncing": SYNC_STATE["is_syncing"]}


# request for syncing only pzpn data
@router.post("/pzpn")
def sync_pzpn(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_sync_process, ["scraper_pzpn.py"])
    return {"status": "started", "message": "PZPN sync started in background."}

#request for syncing only garmin data
@router.post("/garmin")
def sync_garmin(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_sync_process, ["scraper_garmin.py"])
    return {"status": "started", "message": "Garmin sync started in background."}

#request for syncing both
@router.post("/all")
def sync_all_background(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_sync_process, ["scraper_pzpn.py", "scraper_garmin.py"])
    return {"status": "started", "message": "Full sync started in background."}