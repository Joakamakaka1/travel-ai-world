from app.models.meal import Meal
from app.schemas.meal import MealCreate, MealUpdate
from app.services.base import BaseService


class MealService(BaseService[Meal, MealCreate, MealUpdate]):
    pass
