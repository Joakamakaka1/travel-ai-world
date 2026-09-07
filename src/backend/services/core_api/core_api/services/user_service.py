from pydantic import BaseModel

from travel_common.exceptions import Forbidden, Unauthorized
from travel_common.principal import Principal, Role
from core_api.models.user import User
from core_api.repositories.user_repository import UserRepository
from core_api.schemas.user import UserRoleUpdate, UserUpdate
from core_api.services.base import BaseService


class UserService(BaseService[User, BaseModel, UserUpdate | UserRoleUpdate]):
    repository: UserRepository

    async def get_by_email(self, email: str) -> User | None:
        return await self.repository.get_by_email(email)

    async def get_active(self, user_id: int) -> User:
        """Resolve an authenticated caller. 401 (never 404) so IDs don't leak."""
        user = await self.repository.get_by_id(user_id)
        if user is None:
            raise Unauthorized("Invalid authentication credentials")
        if not user.is_active:
            raise Unauthorized("Inactive user account")
        return user

    async def get_owned(self, user_id: int, principal: Principal) -> User:
        """An account may only be managed by its owner."""
        user = await self.get(user_id)
        if user.id != principal.id:
            raise Forbidden()
        return user

    async def find_or_create_google_user(
        self, email: str, google_id: str, name: str, picture: str | None
    ) -> User:
        """Find user by email or create a new Google OAuth user.

        Existing users get their Google profile data refreshed.
        """
        user = await self.repository.get_by_email(email)
        if user:
            user.google_id = google_id
            user.name = name
            user.picture = picture
            user.auth_provider = "google"
            return await self.repository.update(user)

        return await self.repository.create(
            User(
                email=email,
                google_id=google_id,
                name=name,
                picture=picture,
                auth_provider="google",
                is_active=True,
                role=Role.USER,
            )
        )
