from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.core.security.config_updater import config_updater
import logging

logger = logging.getLogger("ConfigAPI")

router = APIRouter()

class ConfigUpdateRequest(BaseModel):
    key: str
    value: str

@router.post("/update")
async def update_env(req: ConfigUpdateRequest):
    """
    Securely updates the .env file with new configuration values.
    """
    try:
        if req.key not in ["MASTER_ENCRYPTION_KEY", "DB_PASSWORD"]:
            raise HTTPException(status_code=403, detail="Not allowed to update this key.")
            
        config_updater.update_env_variable(req.key, req.value)
        return {"status": "success", "message": f"{req.key} updated successfully."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
