import json

from fastapi import FastAPI, HTTPException, Request, status

import uvicorn

webhook_app = FastAPI()


@webhook_app.post("/webhook")
async def receive_webhook(request: Request):
    print("Received Webhook")

    try:
        payload_bytes = await request.body()
        payload_string = payload_bytes.decode("utf-8")
        payload_json = json.loads(payload_string)

        print("Received payload:")
        print(json.dumps(payload_json, indent=4))

        return {"message": "Webhook successfuly received!"}
    except json.JSONDecodeError:
        print("Error, json cannot be parsed!")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error, json cannot be parsed!")
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error, an error occured {e}"
        )

if __name__ == "__main__":
    print("Starting webhook server!")
    uvicorn.run(webhook_app, host="127.0.0.1", port=9000, log_level="info")
