import asyncio
import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import redis.asyncio as redis

router = APIRouter()

redis_client = redis.from_url(
    os.getenv("REDIS_HOST", "redis://localhost:6379/0"),
    decode_responses=True
)


@router.websocket("/notifications/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()

    pubsub = redis_client.pubsub()
    user_channel = f"user-notifications-{user_id}"
    await pubsub.subscribe(user_channel)

    print(f"WebSocket connected for user {user_id} on channel '{user_channel}'")

    try:
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=None
            )

            if message and "data" in message:
                await websocket.send_text(message["data"])
            await asyncio.sleep(0.01)

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        print(f"An error occurred with WebSocket for user {user_id}: {e}")
    finally:
        await pubsub.unsubscribe(user_channel)
        print(f"Unsubscribed from channel '{user_channel}'")
