from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..services.settings_service import SettingsService
from ..schemas.settings import SettingResponse, SettingUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
async def get_all_settings(db: AsyncSession = Depends(get_db)):
    svc = SettingsService(db)
    settings = await svc.get_all()
    return [SettingResponse.model_validate(s) for s in settings]


@router.get("/{key}", response_model=SettingResponse)
async def get_setting(key: str, db: AsyncSession = Depends(get_db)):
    svc = SettingsService(db)
    setting = await svc.get(key)
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return SettingResponse.model_validate(setting)


@router.put("/{key}", response_model=SettingResponse)
async def upsert_setting(key: str, data: SettingUpdate, db: AsyncSession = Depends(get_db)):
    svc = SettingsService(db)
    setting = await svc.upsert(key, data.value, data.description)
    return SettingResponse.model_validate(setting)


@router.delete("/{key}")
async def delete_setting(key: str, db: AsyncSession = Depends(get_db)):
    svc = SettingsService(db)
    deleted = await svc.delete(key)
    if not deleted:
        raise HTTPException(status_code=404, detail="Setting not found")
    return {"message": "Setting deleted"}


@router.post("/reset")
async def reset_settings(db: AsyncSession = Depends(get_db)):
    svc = SettingsService(db)
    await svc.reset()
    return {"message": "Settings reset to defaults"}
