from uuid import UUID

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from psycopg import AsyncConnection

from app.core.security import decode_access_token


security = HTTPBearer()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials

    try:
        user_id = decode_access_token(token)
        user_uuid = UUID(user_id)

    except (ValueError, TypeError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token",
        )

    database_url = request.app.state.database_url

    async with await AsyncConnection.connect(
        database_url
    ) as connection:
        cursor = await connection.execute(
            """
            SELECT
                id,
                name,
                email
            FROM users
            WHERE id = %s;
            """,
            (user_uuid,),
        )

        user = await cursor.fetchone()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User account no longer exists",
        )

    return {
        "id": user[0],
        "name": user[1],
        "email": user[2],
    }
    
async def check_thread_ownership(
    request: Request,
    thread_id: str,
    user_id,
) -> bool:
    database_url = request.app.state.database_url

    async with await AsyncConnection.connect(
        database_url
    ) as connection:
        cursor = await connection.execute(
            """
            SELECT 1
            FROM conversations
            WHERE thread_id = %s
            AND user_id = %s;
            """,
            (thread_id, user_id),
        )

        result = await cursor.fetchone()

    return result is not None