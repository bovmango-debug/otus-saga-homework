import uuid
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
orders = {}

BILLING_URL = "http://billing-service:8000"
WAREHOUSE_URL = "http://warehouse-service:8000"
DELIVERY_URL = "http://delivery-service:8000"

class CreateOrderRequest(BaseModel):
    user_id: str
    item_id: str
    quantity: int
    amount: float
    slot_id: str

@app.get("/orders/{order_id}")
def get_order(order_id: str):
    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")
    return orders[order_id]

@app.post("/orders")
async def create_order(req: CreateOrderRequest):
    order_id = str(uuid.uuid4())
    orders[order_id] = {"order_id": order_id, "status": "PENDING", "details": req.dict()}

    async with httpx.AsyncClient(timeout=5.0) as client:
        pay_res = await client.post(f"{BILLING_URL}/pay", json={
            "order_id": order_id, "user_id": req.user_id, "amount": req.amount
        })
        if pay_res.status_code != 200:
            orders[order_id]["status"] = "CANCELLED_PAYMENT_FAILED"
            raise HTTPException(status_code=400, detail="Payment failed")

        res_res = await client.post(f"{WAREHOUSE_URL}/reserve", json={
            "order_id": order_id, "item_id": req.item_id, "quantity": req.quantity
        })
        if res_res.status_code != 200:
            await client.post(f"{BILLING_URL}/refund", params={"order_id": order_id})
            orders[order_id]["status"] = "CANCELLED_OUT_OF_STOCK"
            raise HTTPException(status_code=400, detail="Warehouse reservation failed, payment refunded")

        del_res = await client.post(f"{DELIVERY_URL}/book", json={
            "order_id": order_id, "slot_id": req.slot_id
        })
        if del_res.status_code != 200:
            await client.post(f"{WAREHOUSE_URL}/release", params={"order_id": order_id})
            await client.post(f"{BILLING_URL}/refund", params={"order_id": order_id})
            orders[order_id]["status"] = "CANCELLED_DELIVERY_UNAVAILABLE"
            raise HTTPException(status_code=400, detail="Delivery booking failed, stock and payment rolled back")

    orders[order_id]["status"] = "COMPLETED"
    return orders[order_id]
