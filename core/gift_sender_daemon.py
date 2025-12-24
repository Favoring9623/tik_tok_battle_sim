#!/usr/bin/env python3
"""
TikTok Gift Sender Daemon
Persistent browser session with REST API control
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from gift_sender import TikTokGiftSender, GiftSendResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state
sender: Optional[TikTokGiftSender] = None
current_task: Optional[Dict[str, Any]] = None
task_history: list = []


class SendGiftRequest(BaseModel):
    """Request model for sending gifts"""
    username: str
    gift_name: str
    quantity: int
    cps: float = 6.0


class SendGiftResponse(BaseModel):
    """Response model for gift sending"""
    success: bool
    message: str
    sent: int = 0
    failed: int = 0
    task_id: Optional[str] = None


class StatusResponse(BaseModel):
    """Current daemon status"""
    connected: bool
    current_streamer: Optional[str]
    current_task: Optional[Dict[str, Any]]
    uptime_seconds: float


# Lifespan management
start_time = datetime.now()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown handlers"""
    global sender
    logger.info("Starting Gift Sender Daemon...")

    # Initialize sender
    sender = TikTokGiftSender()
    await sender.connect(headless=False)
    logger.info("Browser ready!")

    yield

    # Cleanup
    logger.info("Shutting down...")
    if sender:
        await sender.disconnect()


# Create FastAPI app
app = FastAPI(
    title="TikTok Gift Sender API",
    description="REST API for automated TikTok gift sending",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """API info"""
    return {
        "name": "TikTok Gift Sender API",
        "version": "1.0.0",
        "endpoints": {
            "GET /status": "Daemon status",
            "POST /send": "Send gifts",
            "POST /stop": "Stop current task",
            "GET /history": "Task history",
            "POST /navigate": "Navigate to streamer",
        }
    }


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get daemon status"""
    uptime = (datetime.now() - start_time).total_seconds()
    return StatusResponse(
        connected=sender._is_connected if sender else False,
        current_streamer=sender._current_streamer if sender else None,
        current_task=current_task,
        uptime_seconds=uptime
    )


@app.post("/navigate")
async def navigate(username: str):
    """Navigate to a streamer"""
    if not sender or not sender._is_connected:
        raise HTTPException(status_code=503, detail="Daemon not connected")

    success = await sender.go_to_stream(username)
    if not success:
        raise HTTPException(status_code=404, detail=f"@{username} is not live")

    return {"success": True, "streamer": username}


@app.post("/send", response_model=SendGiftResponse)
async def send_gifts(request: SendGiftRequest, background_tasks: BackgroundTasks):
    """Send gifts to a streamer"""
    global current_task

    if not sender or not sender._is_connected:
        raise HTTPException(status_code=503, detail="Daemon not connected")

    if current_task and current_task.get("status") == "running":
        raise HTTPException(status_code=409, detail="A task is already running")

    # Create task
    task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    current_task = {
        "id": task_id,
        "status": "running",
        "username": request.username,
        "gift_name": request.gift_name,
        "quantity": request.quantity,
        "cps": request.cps,
        "sent": 0,
        "failed": 0,
        "started_at": datetime.now().isoformat()
    }

    # Progress callback
    def update_progress(sent, total, failed):
        if current_task:
            current_task["sent"] = sent
            current_task["failed"] = failed
            current_task["progress"] = sent / total * 100

    # Run in background
    async def run_task():
        global current_task
        try:
            result = await sender.send_gifts(
                username=request.username,
                gift_name=request.gift_name,
                quantity=request.quantity,
                cps=request.cps,
                progress_callback=update_progress
            )

            current_task["status"] = "completed" if result.success else "failed"
            current_task["sent"] = result.sent
            current_task["failed"] = result.failed
            current_task["message"] = result.message
            current_task["completed_at"] = datetime.now().isoformat()

            # Add to history
            task_history.append(current_task.copy())
            if len(task_history) > 100:
                task_history.pop(0)

        except Exception as e:
            current_task["status"] = "error"
            current_task["message"] = str(e)

    background_tasks.add_task(run_task)

    return SendGiftResponse(
        success=True,
        message=f"Task started: {request.quantity} {request.gift_name} to @{request.username}",
        task_id=task_id
    )


@app.post("/stop")
async def stop_task():
    """Stop the current task (not fully implemented - need cancellation token)"""
    global current_task
    if not current_task or current_task.get("status") != "running":
        raise HTTPException(status_code=404, detail="No running task")

    current_task["status"] = "stopped"
    current_task["message"] = "Stopped by user"
    return {"success": True, "message": "Task stop requested"}


@app.get("/history")
async def get_history():
    """Get task history"""
    return {"tasks": task_history[-20:]}  # Last 20 tasks


@app.get("/gifts")
async def get_available_gifts():
    """List common gifts"""
    return {
        "bar_gifts": ["Rose", "Fest Cheers", "Fest Party"],
        "panel_gifts": ["Fest Pop", "Money Gun", "Private Jet", "Pyramids", "Interstellar"],
        "recommended_cps": {"safe": 6, "fast": 10, "turbo": 12}
    }


def main():
    """Run the daemon"""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║   🚀 TIKTOK GIFT SENDER DAEMON                                       ║
╠══════════════════════════════════════════════════════════════════════╣
║   API: http://localhost:8888                                         ║
║   Docs: http://localhost:8888/docs                                   ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    uvicorn.run(app, host="0.0.0.0", port=8888)


if __name__ == "__main__":
    main()
