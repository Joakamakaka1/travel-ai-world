"""Google sign-in: exchange a Google ID token for one of our JWTs."""

from fastapi import APIRouter, Depends

from core_api.api.deps import get_user_service
from core_api.auth.google import verify_google_token
from core_api.config import settings
from travel_common.exceptions import Unauthorized
from travel_common.principal import Principal
from travel_common.security import create_access_token
from core_api.schemas.user import GoogleAuthRequest, GoogleAuthResponse
from core_api.services.user_service import UserService

router = APIRouter()


@router.post("/google", response_model=GoogleAuthResponse)
async def google_auth(
    body: GoogleAuthRequest,
    user_service: UserService = Depends(get_user_service),
) -> GoogleAuthResponse:
    """Verify the Google credential, upsert the user and issue our JWT."""
    try:
        google_data = await verify_google_token(body.credential)
    except ValueError as exc:
        raise Unauthorized(str(exc)) from exc

    user = await user_service.find_or_create_google_user(
        email=google_data["email"],
        google_id=google_data["sub"],
        name=google_data.get("name", ""),
        picture=google_data.get("picture"),
    )
    if not user.is_active:
        raise Unauthorized("Inactive user account")

    principal = Principal(id=user.id, email=user.email, role=user.role)
    return GoogleAuthResponse(
        access_token=create_access_token(principal, settings), user=user
    )
