from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
slots = {"slot_10_12": True, "slot_12_14": False}
bookings = {}

class BookRequest(BaseModel):
    order_id: str
    slot_id: str

@app.post("/slots")
def set_slot(slot_id: str, available: bool):
    slots[slot_id] = available
    return {"slot_id": slot_id, "available": slots[slot_id]}

@app.get("/slots/{slot_id}")
def get_slot(slot_id: str):
    return {"slot_id": slot_id, "available": slots.get(slot_id, False)}

@app.post("/book")
def book(req: BookRequest):
    if req.order_id in bookings:
        return {"status": "already_booked"}
    if not slots.get(req.slot_id, False):
        raise HTTPException(status_code=400, detail="Slot unavailable")
    slots[req.slot_id] = False
    bookings[req.order_id] = req.slot_id
    return {"status": "booked"}

@app.post("/cancel")
def cancel(order_id: str):
    slot_id = bookings.pop(order_id, None)
    if slot_id:
        slots[slot_id] = True
    return {"status": "cancelled"}
