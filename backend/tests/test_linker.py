import pytest
from services.linker import find_links

"""Linking matches to trainings is based solely on the date, because it is enough. Referees always have to trainings for 
every half of the match. Training should be linked if it starts form 15 minutes before the match start, to 90 minutes after the start
Halves are later sorted based on when they started"""

def test_find_links_perfect_match():
    """Tests assigment if match starts 10 minutes before it should"""
    matches = [{"mecz_id": "M1", "data_meczu": "2025-10-15 15:00"}]
    trainings = [{"aktywnosc_id": "T1", "data_startu": "2025-10-15 14:50:00"}]

    res = find_links(matches, trainings)

    assert len(res) == 1
    assert res["T1"] == "M1" 

def test_find_links_training_too_early_or_too_late():
    matches = [{"mecz_id": "M1", "data_meczu": "2025-10-15 15:00"}]
    trainings = [
        {"aktywnosc_id": "T1", "data_startu": "2025-10-15 14:00:00"},
        {"aktywnosc_id": "T2", "data_startu": "2025-10-15 17:00:00"}
        ]

    res = find_links(matches, trainings)

    assert len(res) == 0

def test_find_links_trainings_to_one_match():
    matches = [{"mecz_id": "M1", "data_meczu": "2025-10-15 15:00"}]
    trainings = [
        {"aktywnosc_id": "T1", "data_startu": "2025-10-15 15:00:00"},
        {"aktywnosc_id": "T2", "data_startu": "2025-10-15 16:00:00"}
        ]
    
    res = find_links(matches, trainings)

    assert len(res) == 2
    assert res["T1"] == "M1"
    assert res["T2"] == "M1"

def test_find_links_diffrent_day():
    matches = [{"mecz_id": "M1", "data_meczu": "2025-10-15 15:00"}]
    trainings = [{"aktywnosc_id": "T1", "data_startu": "2025-10-16 15:00:00"}]

    res = find_links(matches, trainings)

    assert len(res) == 0


def test_find_links_bad_date_format():
    """Edge Case: Bad data format"""
    matches = [{"mecz_id": "M1", "data_meczu": "USZKODZONA_DATA"}]
    trainings = [{"aktywnosc_id": "T1", "data_startu": "2025-10-15 15:00:00"}]
    
    result = find_links(matches, trainings)

    assert len(result) == 0
    


