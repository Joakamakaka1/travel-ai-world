from core_api.api.v1.api_router import api_router
from core_api.config import settings
from travel_common.http.app_factory import create_app

app = create_app(settings, [api_router])
