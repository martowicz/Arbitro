from db.repo_settings import save_setting, get_setting
from core.security import encrypt_data
from fastapi import APIRouter, HTTPException
from .models import SettingsInput

router = APIRouter(prefix="/api/settings", tags=["Settings"])

@router.post("/")
def update_settings(settings: SettingsInput):
    try:
        #Saving only seetings given by user
        if settings.pzpn_email:
            encrypted_pzpn_email = encrypt_data(settings.pzpn_email)
            save_setting("pzpn_email", encrypted_pzpn_email)

        if settings.pzpn_password:
            encrypted_pzpn_password = encrypt_data(settings.pzpn_password)
            save_setting("pzpn_password", encrypted_pzpn_password)

        if settings.garmin_email:
            encrypted_garmin_email = encrypt_data(settings.garmin_email)
            save_setting("garmin_email", encrypted_garmin_email)
            
        if settings.garmin_password:
            encrypted_garmin_password = encrypt_data(settings.garmin_password)
            save_setting("garmin_password", encrypted_garmin_password)
            
        if settings.openai_api_key:
            encrypted_openai = encrypt_data(settings.openai_api_key)
            save_setting("openai_api_key", encrypted_openai)
        
        if settings.surname_name:
            save_setting("surname_name", settings.surname_name)
            
        return {"status": "success", "message": "Ustawienia zapisane i zaszyfrowane w sejfie."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd zapisu ustawień: {str(e)}")
    
@router.get("/status")
def get_settings_status():
    return {
        "has_pzpn_email": bool(get_setting("pzpn_email")),
        "has_pzpn_password": bool(get_setting("pzpn_password")),
        "has_garmin_email": bool(get_setting("garmin_email")),
        "has_garmin_password": bool(get_setting("garmin_password")),
        "has_openai": bool(get_setting("openai_api_key")),
        "has_surname_name": bool(get_setting("surname_name"))
    }



