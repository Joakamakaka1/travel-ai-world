from ai_api.api.v1.api_router import api_router
from ai_api.config import get_settings
from travel_common.http.app_factory import create_app

app = create_app(get_settings(), [api_router])
