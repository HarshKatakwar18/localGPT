from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    Response,
)

from psycopg import AsyncConnection

from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
)

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
    REFRESH_TOKEN_EXPIRE_DAYS,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


async def get_user_by_email(
    database_url: str,
    email: str,
):
    async with await AsyncConnection.connect(
        database_url
    ) as connection:
        cursor = await connection.execute(
            """
            SELECT
                id,
                name,
                email,
                password_hash
            FROM users
            WHERE email = %s;
            """,
            (email,),
        )

        return await cursor.fetchone()


@router.post(
    "/register",
    response_model=UserResponse,
)
async def register(
    request: RegisterRequest,
):
    from app.main import app

    database_url = app.state.database_url

    name = request.name.strip()
    email = request.email.strip().lower()
    password = request.password

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Name cannot be empty",
        )

    if len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long",
        )

    existing_user = await get_user_by_email(
        database_url,
        email,
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists",
        )

    user_id = uuid4()
    password_hash = hash_password(password)

    async with await AsyncConnection.connect(
        database_url,
        autocommit=True,
    ) as connection:
        await connection.execute(
            """
            INSERT INTO users (
                id,
                name,
                email,
                password_hash
            )
            VALUES (%s, %s, %s, %s);
            """,
            (
                user_id,
                name,
                email,
                password_hash,
            ),
        )

    return UserResponse(
        id=str(user_id),
        name=name,
        email=email,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    request: LoginRequest,
    response: Response,
):
    from app.main import app

    database_url = app.state.database_url

    email = request.email.strip().lower()

    user = await get_user_by_email(
        database_url,
        email,
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    user_id, name, stored_email, stored_password_hash = user

    if not verify_password(
        request.password,
        stored_password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    # Create access token
    access_token = create_access_token(
        str(user_id)
    )

    # Create refresh token
    refresh_token = create_refresh_token()

    refresh_token_hash = hash_refresh_token(
        refresh_token
    )

    refresh_token_id = uuid4()

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    # Store hashed refresh token
    async with await AsyncConnection.connect(
        database_url,
        autocommit=True,
    ) as connection:

        await connection.execute(
            """
            INSERT INTO refresh_tokens (
                id,
                user_id,
                token_hash,
                expires_at
            )
            VALUES (%s, %s, %s, %s);
            """,
            (
                refresh_token_id,
                user_id,
                refresh_token_hash,
                expires_at,
            ),
        )

    # Send refresh token as HttpOnly cookie
    response.set_cookie(
        key="localgpt-refresh-token",
        value=refresh_token,
        httponly=True,
        secure=False,       # True in production HTTPS
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )
    
    
@router.post(
    "/refresh",
    response_model=TokenResponse,
)
async def refresh_access_token(
    request: Request,
    response: Response,
):
    from app.main import app

    database_url = app.state.database_url

    refresh_token = request.cookies.get(
        "localgpt-refresh-token"
    )

    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail="Refresh session not found",
        )

    token_hash = hash_refresh_token(
        refresh_token
    )

    async with await AsyncConnection.connect(
        database_url,
    ) as connection:

        cursor = await connection.execute(
            """
            SELECT
                id,
                user_id,
                expires_at,
                revoked_at
            FROM refresh_tokens
            WHERE token_hash = %s;
            """,
            (token_hash,),
        )

        stored_token = await cursor.fetchone()

    if stored_token is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token",
        )

    token_id, user_id, expires_at, revoked_at = stored_token

    now = datetime.now(timezone.utc)

    if revoked_at is not None:
        raise HTTPException(
            status_code=401,
            detail="Refresh token has been revoked",
        )

    if expires_at <= now:
        raise HTTPException(
            status_code=401,
            detail="Refresh token has expired",
        )

    # Rotate refresh token
    new_refresh_token = create_refresh_token()

    new_refresh_token_hash = hash_refresh_token(
        new_refresh_token
    )

    new_refresh_token_id = uuid4()

    new_expires_at = (
        now
        + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    async with await AsyncConnection.connect(
        database_url,
        autocommit=True,
    ) as connection:

        # Revoke old token
        await connection.execute(
            """
            UPDATE refresh_tokens
            SET revoked_at = NOW()
            WHERE id = %s;
            """,
            (token_id,),
        )

        # Store new token
        await connection.execute(
            """
            INSERT INTO refresh_tokens (
                id,
                user_id,
                token_hash,
                expires_at
            )
            VALUES (%s, %s, %s, %s);
            """,
            (
                new_refresh_token_id,
                user_id,
                new_refresh_token_hash,
                new_expires_at,
            ),
        )

    # New access token
    access_token = create_access_token(
        str(user_id)
    )

    # New refresh cookie
    response.set_cookie(
        key="localgpt-refresh-token",
        value=new_refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )
    
    
@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
):
    from app.main import app

    database_url = app.state.database_url

    refresh_token = request.cookies.get(
        "localgpt-refresh-token"
    )

    if refresh_token:
        token_hash = hash_refresh_token(
            refresh_token
        )

        async with await AsyncConnection.connect(
            database_url,
            autocommit=True,
        ) as connection:

            await connection.execute(
                """
                UPDATE refresh_tokens
                SET revoked_at = NOW()
                WHERE token_hash = %s
                AND revoked_at IS NULL;
                """,
                (token_hash,),
            )

    response.delete_cookie(
        key="localgpt-refresh-token",
        path="/",
    )

    return {
        "message": "Logged out successfully"
    }    