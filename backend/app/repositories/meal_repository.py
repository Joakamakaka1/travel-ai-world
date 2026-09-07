from app.models.meal import Meal
from app.repositories.base import BaseRepository


class MealRepository(BaseRepository[Meal]):
    model = Meal
