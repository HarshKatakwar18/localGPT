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