import pytest
from db.connection import create_all_tables

@pytest.fixture(autouse=True)
def setup_empty_test_db(monkeypatch, tmp_path):
    
    fake_db_path = tmp_path / "testowa_baza_arbitro.db"
    monkeypatch.setattr("db.connection.DB_PATH", str(fake_db_path))
    create_all_tables()
    yield