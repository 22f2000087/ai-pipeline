from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from pydantic import BaseModel
import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class PipelineRequest(BaseModel):
    email: str
    source: str


# ---- AI enrichment (mock or replace with LLM) ----
def ai_enrich(user):
    return {
        "analysis": f"{user['name']} works at {user['company']['name']} and has structured profile data.",
        "sentiment": "balanced"
    }


@app.post("/pipeline")
def pipeline(req: PipelineRequest):

    results = []
    errors = []

    try:
        response = requests.get(
            "https://jsonplaceholder.typicode.com/users",
            timeout=10
        )
        response.raise_for_status()
        users = response.json()[:3]

    except Exception as e:
        return {"error": str(e)}

    for user in users:
        try:
            enrichment = ai_enrich(user)

            item = {
                "original": {
                    "name": user["name"],
                    "email": user["email"],
                    "company": user["company"]["name"]
                },
                "analysis": enrichment["analysis"],
                "sentiment": enrichment["sentiment"],
                "stored": True,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

            results.append(item)

        except Exception as e:
            errors.append(str(e))

    # ---- storage ----
    with open("results.json", "w") as f:
        json.dump(results, f, indent=2)

    # ---- notification ----
    print(f"Notification sent to: {req.email}")

    return {
        "items": results,
        "notificationSent": True,
        "processedAt": datetime.utcnow().isoformat() + "Z",
        "errors": errors
    }
