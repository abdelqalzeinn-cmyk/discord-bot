from fastapi import FastAPI, HTTPException
import uvicorn
from datetime import datetime, timedelta
import requests
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Store monitoring data
monitor_data = {
    "start_time": datetime.utcnow(),
    "request_count": 0,
    "last_checked": None,
    "status_history": []
}

# Health check endpoint
@app.get("/health")
async def health_check():
    monitor_data["request_count"] += 1
    monitor_data["last_checked"] = datetime.utcnow()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "discord-bot",
        "uptime": str(datetime.utcnow() - monitor_data["start_time"]),
        "request_count": monitor_data["request_count"]
    }

# Simple ping endpoint
@app.get("/ping")
async def ping():
    monitor_data["request_count"] += 1
    return {"status": "pong", "timestamp": datetime.utcnow().isoformat()}

# Uptime Kuma compatible endpoint
@app.get("/status")
async def status():
    monitor_data["request_count"] += 1
    return {
        "status": "ok",
        "version": "1.0.0",
        "time": datetime.utcnow().isoformat(),
        "start_time": monitor_data["start_time"].isoformat(),
        "uptime": str(datetime.utcnow() - monitor_data["start_time"])
    }

# Bot status check
@app.get("/bot/status")
async def bot_status():
    try:
        # Try to make a simple API call to the bot
        # You can replace this with an actual endpoint from your bot
        response = requests.get("http://localhost:8000/health", timeout=5)
        response.raise_for_status()
        return {
            "bot_status": "online",
            "response_time_ms": response.elapsed.total_seconds() * 1000,
            "last_checked": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "bot_status": "offline",
            "error": str(e),
            "last_checked": datetime.utcnow().isoformat()
        }

def start_monitor():
    port = int(os.getenv("MONITOR_PORT", 8001))
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
    server = uvicorn.Server(config)
    return server

if __name__ == "__main__":
    port = int(os.getenv("MONITOR_PORT", 8001))
    uvicorn.run("monitor:app", host="0.0.0.0", port=port, reload=True)
