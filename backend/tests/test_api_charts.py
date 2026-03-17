import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

FAKE_CHART_RESPONSE = [
    {
        "title": "Testowy Wykres",
        "chart": {
            "labels": ["00:00", "00:10", "00:20"],
            "datasets": [
                {
                    "label": "Tętno",
                    "data": [120.0, 130.0, 125.0],
                    "borderColor": "red",
                    "backgroundColor": "red",
                    "fill": False,
                    "yAxisID": "y",
                    "tension": 0.4,
                    "pointRadius": 0
                }
            ]
        }
    }
]


MOCK_PATH_DB = "api.charts.fetch_from_db"
MOCK_PATH_UTILS = "api.charts.process_activities_to_charts"


@patch(MOCK_PATH_UTILS)
@patch(MOCK_PATH_DB)
def test_get_match_chart_data_success(mock_fetch_db, mock_process):

    mock_fetch_db.return_value = [{"aktywnosc_id": "ACT_1"}, {"aktywnosc_id": "ACT_2"}]
    
    mock_process.return_value = FAKE_CHART_RESPONSE
    
    response = client.get("/api/matches/MECZ_123/chart_data")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Testowy Wykres"
    
    mock_process.assert_called_once_with([
        ("ACT_1", "Połowa 1", 1), 
        ("ACT_2", "Połowa 2", 2)
    ])

@patch(MOCK_PATH_DB)
def test_get_match_chart_data_not_found(mock_fetch_db):
    mock_fetch_db.return_value = []
    
    response = client.get("/api/matches/MECZ_BLEDNY/chart_data")
    
    assert response.status_code == 404
    assert response.json() == {"detail": "Brak przypisanych połów z Garmina."}

@patch(MOCK_PATH_UTILS)
def test_get_training_chart_data_success(mock_process):
    
    mock_process.return_value = FAKE_CHART_RESPONSE
    
    response = client.get("/api/trainings/TRENING_999/chart_data")
    
    assert response.status_code == 200
    
    mock_process.assert_called_once_with([
        ("TRENING_999", "Dane treningu", None)
    ])