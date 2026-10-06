import uuid
from typing import Any, Generic, TypeVar
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic SQLAlchemy 2.0 repository providing standard CRUD operations."""

    def __init__(self, model_class: type[ModelType], session: AsyncSession):
        self.model_class = model_class
        self.session = session

    async def create(self, entity: ModelType) -> ModelType:
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def get_by_id(self, id: uuid.UUID) -> ModelType | None:
        stmt = select(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, limit: int = 100, offset: int = 0) -> list[ModelType]:
        stmt = select(self.model_class).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, id: uuid.UUID, **values: Any) -> ModelType | None:
        stmt = (
            update(self.model_class)
            .where(self.model_class.id == id)
            .values(**values)
            .returning(self.model_class)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one_or_none()

    async def delete(self, id: uuid.UUID) -> bool:
        stmt = delete(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return bool(result.rowcount and result.rowcount > 0)
