from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.setting import Setting
from shared.config import DEFAULT_SETTINGS


class SettingsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> list[Setting]:
        result = await self.db.execute(select(Setting).order_by(Setting.key))
        return list(result.scalars().all())

    async def get(self, key: str) -> Setting | None:
        return await self.db.get(Setting, key)

    async def upsert(self, key: str, value: dict, description: str | None = None) -> Setting:
        existing = await self.db.get(Setting, key)
        if existing:
            existing.value = value
            if description is not None:
                existing.description = description
        else:
            existing = Setting(key=key, value=value, description=description)
            self.db.add(existing)
        await self.db.commit()
        await self.db.refresh(existing)
        return existing

    async def delete(self, key: str) -> bool:
        setting = await self.db.get(Setting, key)
        if not setting:
            return False
        await self.db.delete(setting)
        await self.db.commit()
        return True

    async def seed_defaults(self) -> None:
        for key, value in DEFAULT_SETTINGS.items():
            existing = await self.db.get(Setting, key)
            if not existing:
                self.db.add(Setting(key=key, value={"v": value}, description="Default"))
        await self.db.commit()

    async def reset(self) -> None:
        await self.db.execute(Setting.__table__.delete())
        await self.seed_defaults()
        await self.db.commit()
