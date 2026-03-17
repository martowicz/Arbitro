import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app

from api.sync import SYNC_STATE  

client = TestClient(app)

MOCK_RUN_SYNC = "api.sync.run_sync_process"


def test_get_sync_status_idle():
    SYNC_STATE["is_syncing"] = False 
    
    response = client.get("/api/sync/status")
    
    assert response.status_code == 200
    assert response.json() == {"is_syncing": False}

def test_get_sync_status_running():
    SYNC_STATE["is_syncing"] = True
    
    response = client.get("/api/sync/status")
    
    assert response.status_code == 200
    assert response.json() == {"is_syncing": True}
    
    SYNC_STATE["is_syncing"] = False


@patch(MOCK_RUN_SYNC)
def test_sync_pzpn_background_task(mock_run_sync):
    
    response = client.post("/api/sync/pzpn")
    
    assert response.status_code == 200
    assert response.json() == {"status": "started", "message": "PZPN sync started in background."}
    
    mock_run_sync.assert_called_once_with(["scraper_pzpn.py"])

@patch(MOCK_RUN_SYNC)
def test_sync_garmin_background_task(mock_run_sync):
    
    response = client.post("/api/sync/garmin")
    
    assert response.status_code == 200
    
    mock_run_sync.assert_called_once_with(["scraper_garmin.py"])

@patch(MOCK_RUN_SYNC)
def test_sync_all_background_task(mock_run_sync):
    
    response = client.post("/api/sync/all")
    
    assert response.status_code == 200
    
    mock_run_sync.assert_called_once_with(["scraper_pzpn.py", "scraper_garmin.py"])