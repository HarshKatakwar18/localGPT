import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    HTTPException
)

from fastapi import Request

from app.api.dependencies import (
    get_current_user,
    check_thread_ownership,
)

from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from fastapi import Depends

from app.api.dependencies import get_current_user

from fastapi import HTTPException

from datetime import datetime, timezone

from psycopg import AsyncConnection

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from langchain_core.messages import AIMessage, HumanMessage

from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.database.users import setup_users_table

from app.agent.graph import build_graph


load_dotenv()


class ChatRequest(BaseModel):
    message: str
    thread_id: str
    
    
class Conversation(BaseModel):
    thread_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    
    
class RenameConversationRequest(BaseModel):
    title: str

    
def message_to_dict(message):
    if isinstance(message, HumanMessage):
        role = "user"
    elif isinstance(message, AIMessage):
        role = "assistant"
    else:
        return None

    return {
        "role": role,
        "content": message.content,
    }


async def setup_conversations_table(database_url: str) -> None:
    async with await AsyncConnection.connect(
        database_url,
        autocommit=True,
    ) as connection:
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                thread_id TEXT PRIMARY KEY,
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        )

        await connection.execute(
            """
            ALTER TABLE conversations
            ADD COLUMN IF NOT EXISTS user_id UUID
            REFERENCES users(id)
            ON DELETE CASCADE;
            """
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    await setup_users_table(database_url)

    await setup_conversations_table(database_url)

    async with AsyncPostgresSaver.from_conn_string(
        database_url
    ) as checkpointer:
        await checkpointer.setup()

        app.state.database_url = database_url
        app.state.checkpointer = checkpointer
        app.state.graph = build_graph(checkpointer)

        yield
        
        
async def save_conversation(
    database_url: str,
    thread_id: str,
    title: str,
    user_id,
) -> None:
    async with await AsyncConnection.connect(
        database_url,
        autocommit=True,
    ) as connection:
        await connection.execute(
            """
            INSERT INTO conversations (
                thread_id,
                user_id,
                title
            )
            VALUES (%s, %s, %s)
            ON CONFLICT (thread_id)
            DO UPDATE SET
                title = EXCLUDED.title,
                updated_at = NOW();
            """,
            (
                thread_id,
                user_id,
                title,
            ),
        )


app = FastAPI(
    title="LocalGPT API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/threads/{thread_id}")
async def get_thread(
    thread_id: str,
    request: Request,
    current_user=Depends(get_current_user),
):
    if not await check_thread_ownership(
        request=request,
        thread_id=thread_id,
        user_id=current_user["id"],
    ):
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    checkpointer = app.state.checkpointer

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    checkpoint_tuple = await checkpointer.aget_tuple(config)

    if checkpoint_tuple is None:
        return {
            "thread_id": thread_id,
            "messages": [],
        }

    checkpoint = checkpoint_tuple.checkpoint

    channel_values = checkpoint.get(
        "channel_values",
        {},
    )

    messages = channel_values.get(
        "messages",
        [],
    )

    serialized_messages = []

    for message in messages:
        converted_message = message_to_dict(message)

        if converted_message:
            serialized_messages.append(
                converted_message
            )

    return {
        "thread_id": thread_id,
        "messages": serialized_messages,
    }

@app.get(
    "/threads",
    response_model=list[Conversation],
)
async def get_threads(
    current_user=Depends(get_current_user),
):
    database_url = app.state.database_url

    async with await AsyncConnection.connect(
        database_url
    ) as connection:
        cursor = await connection.execute(
            """
            SELECT
                thread_id,
                title,
                created_at,
                updated_at
            FROM conversations
            WHERE user_id = %s
            ORDER BY updated_at DESC;
            """,
            (current_user["id"],),
        )

        rows = await cursor.fetchall()

    return [
        Conversation(
            thread_id=row[0],
            title=row[1],
            created_at=row[2],
            updated_at=row[3],
        )
        for row in rows
    ]


@app.post("/chat")
async def chat(
    request: ChatRequest,
    http_request: Request,
    current_user=Depends(get_current_user),
):
    if not await check_thread_ownership(
        request=http_request,
        thread_id=request.thread_id,
        user_id=current_user["id"],
    ):
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    graph = app.state.graph

    result = await graph.ainvoke(
        {
            "messages": [
                ("human", request.message)
            ]
        },
        config={
            "configurable": {
                "thread_id": request.thread_id
            }
        },
    )

    response = result["messages"][-1]

    return {
        "response": response.content
    }


@app.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    http_request: Request,
    current_user=Depends(get_current_user),
):
    database_url = app.state.database_url

    # Check whether this conversation already exists.
    async with await AsyncConnection.connect(
        database_url
    ) as connection:
        cursor = await connection.execute(
            """
            SELECT user_id
            FROM conversations
            WHERE thread_id = %s;
            """,
            (request.thread_id,),
        )

        existing_conversation = await cursor.fetchone()

    # Existing conversation
    if existing_conversation is not None:
        existing_user_id = existing_conversation[0]

        if existing_user_id != current_user["id"]:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )

    # New conversation OR legacy conversation
    await save_conversation(
        database_url=database_url,
        thread_id=request.thread_id,
        title=request.message[:40],
        user_id=current_user["id"],
    )

    graph = app.state.graph

    async def generate():
        async for event in graph.astream_events(
            {"messages": [("human", request.message)]},
            config={
                "configurable": {
                    "thread_id": request.thread_id,
                }
            },
            version="v2",
        ):
            if event["event"] != "on_chat_model_stream":
                continue

            chunk = event["data"]["chunk"]

            if chunk.content:
                yield chunk.content

    return StreamingResponse(
        generate(),
        media_type="text/plain",
    )
    
    
@app.patch("/threads/{thread_id}")
async def rename_thread(
    thread_id: str,
    request: RenameConversationRequest,
    http_request: Request,
    current_user=Depends(get_current_user),
):
    if not await check_thread_ownership(
        request=http_request,
        thread_id=thread_id,
        user_id=current_user["id"],
    ):
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    title = request.title.strip()

    if not title:
        raise HTTPException(
            status_code=400,
            detail="Conversation title cannot be empty",
        )

    await save_conversation(
        database_url=app.state.database_url,
        thread_id=thread_id,
        title=title[:100],
        user_id=current_user["id"],
    )

    return {
        "thread_id": thread_id,
        "title": title[:100],
    }
    
    

@app.delete("/threads/{thread_id}")
async def delete_thread(
    thread_id: str,
    request: Request,
    current_user=Depends(get_current_user),
):
    if not await check_thread_ownership(
        request=request,
        thread_id=thread_id,
        user_id=current_user["id"],
    ):
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    database_url = app.state.database_url

    async with await AsyncConnection.connect(
        database_url,
        autocommit=False,
    ) as connection:
        try:
            # Delete checkpoint writes first because they may depend
            # on checkpoint records.
            await connection.execute(
                """
                DELETE FROM checkpoint_writes
                WHERE thread_id = %s;
                """,
                (thread_id,),
            )

            # Delete checkpoint records for this thread.
            await connection.execute(
                """
                DELETE FROM checkpoints
                WHERE thread_id = %s;
                """,
                (thread_id,),
            )

            # Delete stored checkpoint blobs for this thread.
            await connection.execute(
                """
                DELETE FROM checkpoint_blobs
                WHERE thread_id = %s;
                """,
                (thread_id,),
            )

            # Delete the frontend conversation metadata.
            result = await connection.execute(
                """
                DELETE FROM conversations
                WHERE thread_id = %s;
                """,
                (thread_id,),
            )

            await connection.commit()

        except Exception:
            await connection.rollback()
            raise HTTPException(
                status_code=500,
                detail="Failed to permanently delete the conversation",
            )

    return {
        "message": "Conversation and checkpoint data deleted permanently",
        "thread_id": thread_id,
    }