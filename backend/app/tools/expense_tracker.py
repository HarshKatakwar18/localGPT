from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from psycopg import AsyncConnection


ExpenseOperation = Literal["add", "list", "summary"]


@tool
async def expense_tracker(
    operation: ExpenseOperation,
    config: RunnableConfig,
    amount: float | None = None,
    category: str | None = None,
    subcategory: str | None = None,
    description: str | None = None,
    merchant: str | None = None,
    expense_date: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    """
    Track and analyze the user's personal expenses.

    Operations:

    - add:
      Add a new expense to the user's expense records.

    - list:
      Retrieve individual expenses for a date range.

    - summary:
      Calculate total spending and category-wise spending for a date range.

    Dates must use YYYY-MM-DD format.

    Categories should use simple categories such as:
    Housing & Utilities,
    Food & Groceries,
    Transportation,
    Personal & Lifestyle,
    Shopping,
    Travel,
    Education,
    Financial,
    Family & Gifts,
    Other.
    """

    user_id = config.get("configurable", {}).get("user_id")
    database_url = config.get("configurable", {}).get("database_url")

    if not user_id:
        return "Expense tracking is unavailable because the user could not be identified."

    if not database_url:
        return "Expense tracking is unavailable because the database configuration is missing."

    try:
        user_uuid = UUID(str(user_id))
    except ValueError:
        return "Expense tracking failed because the user ID is invalid."

    try:
        if operation == "add":
            return await _add_expense(
                database_url=database_url,
                user_id=user_uuid,
                amount=amount,
                category=category,
                subcategory=subcategory,
                description=description,
                merchant=merchant,
                expense_date=expense_date,
            )

        if operation == "list":
            return await _list_expenses(
                database_url=database_url,
                user_id=user_uuid,
                start_date=start_date,
                end_date=end_date,
            )

        if operation == "summary":
            return await _expense_summary(
                database_url=database_url,
                user_id=user_uuid,
                start_date=start_date,
                end_date=end_date,
            )

        return "Unsupported expense operation."

    except Exception:
        return "Expense tracking failed while accessing the expense records."


async def _add_expense(
    database_url: str,
    user_id: UUID,
    amount: float | None,
    category: str | None,
    subcategory: str | None,
    description: str | None,
    merchant: str | None,
    expense_date: str | None,
) -> str:
    if amount is None or amount <= 0:
        return "Please provide a valid positive expense amount."

    if not category:
        return "Please provide an expense category."

    if not subcategory:
        return "Please provide an expense subcategory."

    if not description:
        return "Please provide a short description of the expense."

    if not expense_date:
        return "Please provide the expense date in YYYY-MM-DD format."

    try:
        parsed_date = date.fromisoformat(expense_date)
    except ValueError:
        return "Invalid expense date. Use YYYY-MM-DD format."

    amount_decimal = Decimal(str(amount)).quantize(Decimal("0.01"))

    async with await AsyncConnection.connect(database_url) as connection:
        cursor = await connection.execute(
            """
            INSERT INTO expenses (
                user_id,
                amount,
                currency,
                category,
                subcategory,
                description,
                merchant,
                expense_date
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING
                id,
                amount,
                currency,
                category,
                subcategory,
                description,
                merchant,
                expense_date;
            """,
            (
                user_id,
                amount_decimal,
                "INR",
                category.strip(),
                subcategory.strip(),
                description.strip(),
                merchant.strip() if merchant else None,
                parsed_date,
            ),
        )

        row = await cursor.fetchone()
        await connection.commit()

    return (
        "Expense added successfully.\n"
        f"Amount: ₹{row[1]:,.2f}\n"
        f"Category: {row[3]}\n"
        f"Subcategory: {row[4]}\n"
        f"Description: {row[5]}\n"
        f"Date: {row[7].isoformat()}"
        + (f"\nMerchant: {row[6]}" if row[6] else "")
    )


async def _list_expenses(
    database_url: str,
    user_id: UUID,
    start_date: str | None,
    end_date: str | None,
) -> str:
    parsed_start = _parse_date(start_date)
    parsed_end = _parse_date(end_date)

    if start_date and not parsed_start:
        return "Invalid start date. Use YYYY-MM-DD format."

    if end_date and not parsed_end:
        return "Invalid end date. Use YYYY-MM-DD format."

    if parsed_start and parsed_end and parsed_start > parsed_end:
        return "Start date cannot be later than end date."

    conditions = ["user_id = %s"]
    parameters: list[object] = [user_id]

    if parsed_start:
        conditions.append("expense_date >= %s")
        parameters.append(parsed_start)

    if parsed_end:
        conditions.append("expense_date <= %s")
        parameters.append(parsed_end)

    where_clause = " AND ".join(conditions)

    async with await AsyncConnection.connect(database_url) as connection:
        cursor = await connection.execute(
            f"""
            SELECT
                expense_date,
                amount,
                currency,
                category,
                subcategory,
                description,
                merchant
            FROM expenses
            WHERE {where_clause}
            ORDER BY expense_date DESC, created_at DESC;
            """,
            parameters,
        )

        rows = await cursor.fetchall()

    if not rows:
        return "No expenses were found for the requested period."

    lines = ["Expense records:"]

    for row in rows:
        merchant_text = f" | Merchant: {row[6]}" if row[6] else ""

        lines.append(
            f"- {row[0].isoformat()} | "
            f"₹{row[1]:,.2f} {row[2]} | "
            f"{row[3]} | "
            f"{row[4]} | "
            f"{row[5]}"
            f"{merchant_text}"
        )

    return "\n".join(lines)


async def _expense_summary(
    database_url: str,
    user_id: UUID,
    start_date: str | None,
    end_date: str | None,
) -> str:
    parsed_start = _parse_date(start_date)
    parsed_end = _parse_date(end_date)

    if start_date and not parsed_start:
        return "Invalid start date. Use YYYY-MM-DD format."

    if end_date and not parsed_end:
        return "Invalid end date. Use YYYY-MM-DD format."

    if parsed_start and parsed_end and parsed_start > parsed_end:
        return "Start date cannot be later than end date."

    conditions = ["user_id = %s"]
    parameters: list[object] = [user_id]

    if parsed_start:
        conditions.append("expense_date >= %s")
        parameters.append(parsed_start)

    if parsed_end:
        conditions.append("expense_date <= %s")
        parameters.append(parsed_end)

    where_clause = " AND ".join(conditions)

    async with await AsyncConnection.connect(database_url) as connection:
        total_cursor = await connection.execute(
            f"""
            SELECT
                COUNT(*),
                COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE {where_clause};
            """,
            parameters,
        )

        total_row = await total_cursor.fetchone()

        category_cursor = await connection.execute(
            f"""
            SELECT
                category,
                COUNT(*),
                COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE {where_clause}
            GROUP BY category
            ORDER BY SUM(amount) DESC;
            """,
            parameters,
        )

        category_rows = await category_cursor.fetchall()

    transaction_count = total_row[0]
    total_amount = total_row[1]

    if transaction_count == 0:
        return "No expenses were found for the requested period."

    lines = [
        "Expense summary:",
        f"Total spending: ₹{total_amount:,.2f}",
        f"Number of expenses: {transaction_count}",
        "",
        "Category breakdown:",
    ]

    for row in category_rows:
        lines.append(
            f"- {row[0]}: ₹{row[2]:,.2f} ({row[1]} transactions)"
        )

    return "\n".join(lines)


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None

    try:
        return date.fromisoformat(value)
    except ValueError:
        return None