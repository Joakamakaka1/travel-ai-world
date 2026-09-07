from sqlalchemy import select

from core_api.models.trip import Trip
from core_api.repositories.base import BaseRepository


class TripRepository(BaseRepository[Trip]):
    model = Trip

    async def get_by_user(
        self, user_id: int, *, skip: int = 0, limit: int = 100
    ) -> list[Trip]:
        stmt = select(Trip).where(Trip.user_id == user_id).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
