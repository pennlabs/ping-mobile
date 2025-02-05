from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List
import time
import jwt
import requests
import os

app = FastAPI()
security = HTTPBearer()

PINGMOBILE_SECRET = os.getenv("PINGMOBILE_SECRET")
if not PINGMOBILE_SECRET:
    raise ValueError("PINGMOBILE_SECRET environment variable is not set")

PINGMOBILE_PEM = os.getenv("PINGMOBILE_PEM")
if not PINGMOBILE_PEM:
    raise ValueError("PINGMOBILE_PEM environment variable is not set")

ALLOWED_USERS = {"joyliu", "antli", "vcai", "jhawkman", "melitski"}


class NotificationRequest(BaseModel):
    recipients: List[str]
    title: str
    body: str


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, PINGMOBILE_SECRET, algorithms=["HS256"])
        if payload["pennkey"] not in ALLOWED_USERS:
            raise HTTPException(status_code=403, detail="User not authorized")
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/api/notifications/ping")
def ping():
    return {"status": "ok"}

@app.post("/api/notifications/generate_token/{pennkey}")
def generate_token(pennkey: str):
    if pennkey not in ALLOWED_USERS:
        raise HTTPException(status_code=403, detail="User not authorized")
    
    payload = {
        "pennkey": pennkey,
    }
    token = jwt.encode(payload, PINGMOBILE_SECRET, algorithm="HS256")
    return {"token": token}

@app.post("/api/notifications/send_notification")
def send_notification(req: NotificationRequest, token_payload: dict = Depends(verify_token)):
    private_key = PINGMOBILE_PEM

    now = int(time.time())
    payload = {
        "use": "access",
        "sub": "urn:pennlabs:alert",
        "exp": now + 3600,  # Expires in 1 hour
    }

    token = jwt.encode(payload, private_key, algorithm="RS256")
    print("Generated Token:", token)

    endpoint = "https://pennmobile.org/api/user/notifications/alerts/"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    data = {
        "users": req.recipients,
        "service": "COURSES",
        "title": req.title,
        "body": req.body,
    }

    response = requests.post(endpoint, headers=headers, json=data)

    try:
        return response.json()
    except Exception:
        return {"status_code": response.status_code, "text": response.text}


# For local testing, run:
#   uvicorn main:app --reload
#
# Then send a POST request (e.g., via curl or a tool like Postman) to:
#   http://127.0.0.1:8000/send_notification
# with JSON body, for example:
# {
#   "recipients": ["alice", "bob"],
#   "title": "Test Notification",
#   "body": "Hello from FastAPI!"
# }
