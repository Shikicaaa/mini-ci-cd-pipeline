from fastapi import APIRouter, Request, Depends
from sse_starlette.sse import EventSourceResponse
import asyncio
import redis.asyncio as aioredis
import json
import os

router = APIRouter()


async def get_redis_connection():
    redis_url = os.getenv("REDIS_URL")
    client = await aioredis.from_url(redis_url)
    try:
        yield client
    finally:
        await client.close()


@router.get("/user/{user_id}")
async def pipeline_events_sse(
    request: Request,
    user_id: str,
    redis: aioredis.Redis = Depends(get_redis_connection)
):
    redis_url = os.environ.get("REDIS_URL")

    async def event_stream():
        local_redis = await aioredis.from_url(redis_url)
        pubsub = local_redis.pubsub()

        redis_channel = f"user-notifications-{user_id}"
        await pubsub.subscribe(redis_channel)
        print(f"Subscribed to channel: {redis_channel}")

        try:
            while True:
                if await request.is_disconnected():
                    print(f"SSE for user {user_id} disconnected")
                    break
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1
                )
                if message and message['type'] == 'message':
                    message_data_str = message['data']
                    if isinstance(message_data_str, bytes):
                        message_data_str = message_data_str.decode('utf-8')

                    event_data = json.loads(message_data_str)
                    yield {
                        "event": "user_notification",
                        "data": json.dumps(event_data)
                    }
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            print(f"SSE for user {user_id} cancelled")
        except Exception as e:
            print(f"Error in SSE event_stream for user={user_id}: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }
        finally:
            print(f"Unsubscribing SSE client from Redis channel: {redis_channel}")
            if pubsub.subscribed:
                await pubsub.unsubscribe(redis_channel)
            await local_redis.close()
            print(f"Redis connection closed for SSE client (user={user_id})")
    return EventSourceResponse(event_stream())
