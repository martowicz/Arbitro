import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app  # Upewnij się, że importujesz poprawną instancję aplikacji

client = TestClient(app)

# =======================================================
# HELPERS (Dane testowe, żeby nie powtarzać kodu)
# =======================================================

def get_base_mock_match():
    return {
        "mecz_id": "M1",
        "data_meczu": "2020-01-01 12:00",
        "gospodarze": "Team A",
        "goscie": "Team B",
        "liga": "Ekstraklasa",
        "rola": "Sędzia",
        "full_distance": 10.5,
        "average_heart_rate": 150,
        "full_calories": 800,
        "full_time": 90
    }

def get_base_mock_training():
    return {
        "aktywnosc_id": "T1",
        "typ": "running",
        "data_startu": "2020-01-02 12:00:00",
        "nazwa": "Poranny Bieg",
        "czas_min": 45,
        "dystans_km": 5.0,
        "tetno_sr": 140,
        "kalorie": 400
    }

MOCK_PATH_MATCHES = "api.events.fetch_matches_for_display"
MOCK_PATH_TRAININGS = "api.events.fetch_trainings_for_display"
MOCK_PATH_SETTINGS = "api.events.get_setting"

@patch(MOCK_PATH_TRAININGS)
@patch(MOCK_PATH_MATCHES)
@patch(MOCK_PATH_SETTINGS)
def test_get_events_empty_database(mock_settings, mock_matches, mock_trainings):
    """Test 1: Ensures the endpoint returns an empty list (200 OK) when there are no records."""
    mock_settings.return_value = "Jan Kowalski"
    mock_matches.return_value = []
    mock_trainings.return_value = []

    response = client.get("/api/events")
    
    assert response.status_code == 200
    assert response.json() == []

@patch(MOCK_PATH_TRAININGS)
@patch(MOCK_PATH_MATCHES)
@patch(MOCK_PATH_SETTINGS)
def test_categorize_past_match(mock_settings, mock_matches, mock_trainings):
    """Test 2: Ensures matches older than current date are categorized as 'past_matches'."""
    mock_settings.return_value = "Jan Kowalski"
    mock_trainings.return_value = []
    
    # Very old date
    match = get_base_mock_match()
    match["data_meczu"] = "1999-01-01 12:00" 
    mock_matches.return_value = [match]

    response = client.get("/api/events")
    data = response.json()
    
    assert len(data) == 1
    assert data[0]["entry_type"] == "past_matches"

@patch(MOCK_PATH_TRAININGS)
@patch(MOCK_PATH_MATCHES)
@patch(MOCK_PATH_SETTINGS)
def test_categorize_upcoming_match(mock_settings, mock_matches, mock_trainings):
    """Test 3: Ensures matches in the future are categorized as 'upcoming_matches'."""
    mock_settings.return_value = "Jan Kowalski"
    mock_trainings.return_value = []
    
    # Very futuristic date
    match = get_base_mock_match()
    match["data_meczu"] = "2099-12-31 12:00" 
    mock_matches.return_value = [match]

    response = client.get("/api/events")
    data = response.json()
    
    assert data[0]["entry_type"] == "upcoming_matches"

@patch(MOCK_PATH_TRAININGS)
@patch(MOCK_PATH_MATCHES)
@patch(MOCK_PATH_SETTINGS)
def test_training_emoji_running(mock_settings, mock_matches, mock_trainings):
    """Test 4: Ensures 'running' type assigns the correct 🏃 emoji."""
    mock_settings.return_value = "Jan Kowalski"
    mock_matches.return_value = []
    
    training = get_base_mock_training()
    training["typ"] = "running"
    training["nazwa"] = "Szybki Bieg"
    mock_trainings.return_value = [training]

    response = client.get("/api/events")
    data = response.json()
    
    assert data[0]["title"] == "🏃 Szybki Bieg"

@patch(MOCK_PATH_TRAININGS)
@patch(MOCK_PATH_MATCHES)
@patch(MOCK_PATH_SETTINGS)
def test_training_emoji_cycling(mock_settings, mock_matches, mock_trainings):
    """Test 5: Ensures 'cycling' type assigns the correct 🚴 emoji."""
    mock_settings.return_value = "Jan Kowalski"
    mock_matches.return_value = []
    
    training = get_base_mock_training()
    training["typ"] = "cycling"
    training["nazwa"] = "Rower"
    mock_trainings.return_value = [training]

    response = client.get("/api/events")
    data = response.json()
    
    assert data[0]["title"] == "🚴 Rower"

@patch(MOCK_PATH_TRAININGS)
@patch(MOCK_PATH_MATCHES)
@patch(MOCK_PATH_SETTINGS)
def test_training_emoji_other(mock_settings, mock_matches, mock_trainings):
    """Test 6: Ensures any other training type defaults to the 💪 emoji."""
    mock_settings.return_value = "Jan Kowalski"
    mock_matches.return_value = []
    
    training = get_base_mock_training()
    training["typ"] = "strength_training" # Unrecognized type
    training["nazwa"] = "Siłownia"
    mock_trainings.return_value = [training]

    response = client.get("/api/events")
    data = response.json()
    
    assert data[0]["title"] == "💪 Siłownia"

@patch(MOCK_PATH_TRAININGS)
@patch(MOCK_PATH_MATCHES)
@patch(MOCK_PATH_SETTINGS)
def test_null_values_fallback(mock_settings, mock_matches, mock_trainings):
    """Test 7: Edge case - tests if the system handles 'None' values from DB by replacing them with 0.0 or 00:00."""
    mock_settings.return_value = "Jan Kowalski"
    mock_trainings.return_value = []
    
    match = get_base_mock_match()
    # Missing statistics
    match["full_distance"] = None
    match["average_heart_rate"] = None
    match["full_calories"] = None
    match["full_time"] = None
    
    mock_matches.return_value = [match]

    response = client.get("/api/events")
    data = response.json()
    
    assert data[0]["distance"] == 0.0
    assert data[0]["heart_rate"] == 0.0
    assert data[0]["calories"] == 0.0
    assert data[0]["time"] == "00:00"

@patch(MOCK_PATH_TRAININGS)
@patch(MOCK_PATH_MATCHES)
@patch(MOCK_PATH_SETTINGS)
def test_sorting_descending_by_date(mock_settings, mock_matches, mock_trainings):
    """Test 8: Ensures all events are sorted chronologically from newest to oldest."""
    mock_settings.return_value = "Jan Kowalski"
    
    match_old = get_base_mock_match()
    match_old["data_meczu"] = "2024-01-01 10:00"
    
    match_new = get_base_mock_match()
    match_new["data_meczu"] = "2024-03-01 10:00"
    
    training_middle = get_base_mock_training()
    training_middle["data_startu"] = "2024-02-01 10:00:00"

    mock_matches.return_value = [match_old, match_new]
    mock_trainings.return_value = [training_middle]

    response = client.get("/api/events")
    data = response.json()
    
    assert len(data) == 3
    # The newest should be first
    assert data[0]["date"] == "2024-03-01 10:00"
    assert data[1]["date"][:10] == "2024-02-01" # Training date slicing
    assert data[2]["date"] == "2024-01-01 10:00"