from datetime import datetime, timezone
from uuid import UUID, uuid4


class User:
    def __init__(
        self,
        id: UUID | None = None,
        name: str = "",
        email: str = "",
        password_hash: str = "",
        created_at: datetime | None = None,
    ):
        self.id = id or uuid4()
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at or datetime.now(timezone.utc)