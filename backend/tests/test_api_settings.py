from fastapi.testclient import TestClient
from main import app
import pytest

client = TestClient(app)



def test_get_settings_endpoint():
    response = client.get("/api/settings/status")
    
    assert response.status_code == 200
    assert isinstance(response.json(), dict)

def test_post_settings_partial_update():
    valid_partial_payload_1 = {"pzpn_email": "nowy_testowy@arbitro.pl"}
    valid_partial_payload_2 = {"pzpn_password": "nowy_testowy@arbitro.pl"}
    valid_partial_payload_3 = {"garmin_email": "nowy_testowy@arbitro.pl"}
    valid_partial_payload_4 = {"garmin_password": "nowy_testowy@arbitro.pl"}
    
    response = client.post("/api/settings", json=valid_partial_payload_1)
    assert response.status_code == 200
    response = client.post("/api/settings", json=valid_partial_payload_2)
    assert response.status_code == 200
    response = client.post("/api/settings", json=valid_partial_payload_3)
    assert response.status_code == 200
    response = client.post("/api/settings", json=valid_partial_payload_4)
    assert response.status_code == 200

def test_post_settings_truly_invalid_data():
    
    response = client.post("/api/settings", content="This is not valid data at all")
    assert response.status_code == 422

def test_post_settings_invalid_json():
    invalid_json = {"not_valid": "not_valid"}
    response = client.post("/api/settings", json=invalid_json)
    assert response.status_code == 422

def test_post_then_get_settings_exact_match():
    test_payload = {
        "pzpn_email": "moj_nowy_testowy_mail@arbitro.pl",
        "pzpn_password": "ZupelnieNoweHaslo123!"
    }
    
    client.post("/api/settings", json=test_payload)
    get_response = client.get("/api/settings/status")
    
    returned_data = get_response.json()
    
    assert returned_data["has_pzpn_email"] is True
    assert returned_data["has_pzpn_password"] is True
    assert returned_data["has_garmin_email"] is False
    assert returned_data["has_surname_name"] is False
    assert returned_data["has_openai"] is False

def test_partial_updates_do_not_overwrite_each_other():
    client.post("/api/settings", json={"pzpn_email": "my.address@arbitro.pl"})
    
    intermediate_state = client.get("/api/settings/status").json()
    assert intermediate_state["has_pzpn_email"] is True
    assert intermediate_state["has_pzpn_password"] is False
    
    client.post("/api/settings", json={"pzpn_password": "SecretPassword123!"})
    
    final_state = client.get("/api/settings/status").json()
    
    assert final_state["has_pzpn_password"] is True
    assert final_state["has_pzpn_email"] is True