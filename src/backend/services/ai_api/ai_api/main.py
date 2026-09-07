from ai_api.api.v1.api_router import api_router
from ai_api.config import get_settings
from travel_common.http.app_factory import create_app

settings = get_settings()
app = create_app(
    settings,
    [api_router],
    docs_prefix=f"{settings.API_V1_STR}{api_router.prefix}",
)
