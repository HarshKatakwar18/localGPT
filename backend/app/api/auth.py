from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException

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

    access_token = create_access_token(
        str(user_id)
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )