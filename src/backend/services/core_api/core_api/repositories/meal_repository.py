from core_api.models.meal import Meal
from core_api.repositories.base import BaseRepository


class MealRepository(BaseRepository[Meal]):
    model = Meal
