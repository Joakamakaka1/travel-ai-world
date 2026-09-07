"""Generic business layer over a repository.

Services receive an already-built repository (dependency inversion) and
raise domain errors; they never know about HTTP.
"""

from typing import Any

from pydantic import BaseModel

from app.core.exceptions import EntityNotFound
from app.models.base import Base
from app.repositories.base import BaseRepository


class BaseService[ModelT: Base, CreateT: BaseModel, UpdateT: BaseModel]:
    entity_name: str | None = None

    def __init__(self, repository: BaseRepository[ModelT]) -> None:
        self.repository = repository

    @property
    def _entity(self) -> str:
        return self.entity_name or self.repository.model.__name__

    async def get(self, obj_id: Any) -> ModelT:
        obj = await self.repository.get_by_id(obj_id)
        if obj is None:
            raise EntityNotFound(self._entity, obj_id)
        return obj

    async def list(self, *, skip: int = 0, limit: int = 100) -> list[ModelT]:
        return await self.repository.get_all(skip=skip, limit=limit)

    async def create(self, data: CreateT, **context: Any) -> ModelT:
        """Create from a schema; `context` carries server-side fields (owner ids)."""
        return await self.repository.create(
            self.repository.model(**data.model_dump(), **context)
        )

    async def update(self, obj: ModelT, data: UpdateT) -> ModelT:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        return await self.repository.update(obj)

    async def delete(self, obj: ModelT) -> None:
        await self.repository.delete(obj)
