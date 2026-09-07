from core_api.models.meal import Meal
from core_api.schemas.meal import MealCreate, MealUpdate
from core_api.services.base import BaseService


class MealService(BaseService[Meal, MealCreate, MealUpdate]):
    pass
