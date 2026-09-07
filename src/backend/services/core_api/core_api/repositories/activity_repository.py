from core_api.models.activity import Activity
from core_api.repositories.base import BaseRepository


class ActivityRepository(BaseRepository[Activity]):
    model = Activity
