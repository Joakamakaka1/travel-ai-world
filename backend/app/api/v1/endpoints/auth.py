"""Google sign-in: exchange a Google ID token for one of our JWTs."""

from fastapi import APIRouter, Depends

from app.api.deps import get_user_service
from app.auth.google import verify_google_token
from app.core.exceptions import Unauthorized
from app.core.principal import Principal
from app.core.security import create_access_token
from app.schemas.user import GoogleAuthRequest, GoogleAuthResponse
from app.services.user_service import UserService

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
    return GoogleAuthResponse(access_token=create_access_token(principal), user=user)
