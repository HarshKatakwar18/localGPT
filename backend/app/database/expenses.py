from psycopg import AsyncConnection


async def setup_expenses_table(database_url: str) -> None:
    async with await AsyncConnection.connect(
        database_url,
        autocommit=True,
    ) as connection:
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

                user_id UUID NOT NULL
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                amount NUMERIC(12, 2) NOT NULL
                    CHECK (amount > 0),

                currency VARCHAR(3) NOT NULL DEFAULT 'INR',

                category TEXT NOT NULL,

                subcategory TEXT NOT NULL,

                description TEXT NOT NULL,

                merchant TEXT,

                expense_date DATE NOT NULL,

                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        )

        await connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_expenses_user_date
            ON expenses(user_id, expense_date);
            """
        )

        await connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_expenses_user_category
            ON expenses(user_id, category);
            """
        )