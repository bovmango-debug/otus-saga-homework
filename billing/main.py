from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
accounts = {"user_1": 1000.0}
transactions = {}

class PayRequest(BaseModel):
    order_id: str
    user_id: str
    amount: float

@app.post("/deposit")
def deposit(user_id: str, amount: float):
    accounts[user_id] = accounts.get(user_id, 0.0) + amount
    return {"user_id": user_id, "balance": accounts[user_id]}

@app.get("/balance/{user_id}")
def get_balance(user_id: str):
    return {"user_id": user_id, "balance": accounts.get(user_id, 0.0)}

@app.post("/pay")
def pay(req: PayRequest):
    if req.order_id in transactions:
        return {"status": "already_paid"}
    balance = accounts.get(req.user_id, 0.0)
    if balance < req.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    accounts[req.user_id] = balance - req.amount
    transactions[req.order_id] = req
    return {"status": "paid", "balance": accounts[req.user_id]}

@app.post("/refund")
def refund(order_id: str):
    tx = transactions.pop(order_id, None)
    if tx:
        accounts[tx.user_id] = accounts.get(tx.user_id, 0.0) + tx.amount
    return {"status": "refunded"}
