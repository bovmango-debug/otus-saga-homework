from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
stock = {"item_1": 5}
reservations = {}

class ReserveRequest(BaseModel):
    order_id: str
    item_id: str
    quantity: int

@app.post("/stock")
def set_stock(item_id: str, quantity: int):
    stock[item_id] = quantity
    return {"item_id": item_id, "quantity": stock[item_id]}

@app.get("/stock/{item_id}")
def get_stock(item_id: str):
    return {"item_id": item_id, "quantity": stock.get(item_id, 0)}

@app.post("/reserve")
def reserve(req: ReserveRequest):
    if req.order_id in reservations:
        return {"status": "already_reserved"}
    available = stock.get(req.item_id, 0)
    if available < req.quantity:
        raise HTTPException(status_code=400, detail="Out of stock")
    stock[req.item_id] = available - req.quantity
    reservations[req.order_id] = req
    return {"status": "reserved", "remaining": stock[req.item_id]}

@app.post("/release")
def release(order_id: str):
    res = reservations.pop(order_id, None)
    if res:
        stock[res.item_id] = stock.get(res.item_id, 0) + res.quantity
    return {"status": "released"}
