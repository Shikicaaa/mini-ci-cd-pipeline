from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def read_root():
    return {"message": "Hello World"}


@app.get("/status")
async def get_Status():
    return {"status": "OK"}


@app.get("/item/{item_id}")
async def get_item(
    item_id: int,
    query_param: str | None = None
):
    return {"item_id": item_id, "query_param": query_param}
