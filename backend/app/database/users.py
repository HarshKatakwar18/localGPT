from psycopg import AsyncConnection


async def setup_users_table(database_url: str) -> None:

    async with await AsyncConnection.connect(
        database_url,
        autocommit=True,
    ) as connection:

        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        )


async def setup_refresh_tokens_table(database_url: str) -> None:

    async with await AsyncConnection.connect(
        database_url,
        autocommit=True,
    ) as connection:

        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                token_hash TEXT NOT NULL UNIQUE,

                expires_at TIMESTAMPTZ NOT NULL,

                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

                revoked_at TIMESTAMPTZ
            );

            CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id
            ON refresh_tokens(user_id);

            CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_hash
            ON refresh_tokens(token_hash);
            """
        )