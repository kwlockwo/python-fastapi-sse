from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from datetime import datetime
from typing import AsyncGenerator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS for SSE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


class SSEMessage:
    """Helper class to format SSE messages"""
    
    @staticmethod
    def format(data: dict, event: str = None, id: str = None, retry: int = None) -> str:
        """
        Format data as SSE message.
        SSE format:
        event: <event_type>
        id: <message_id>
        retry: <reconnection_time_ms>
        data: <json_data>
        
        (blank line to signal end of message)
        """
        message = ""
        
        if event:
            message += f"event: {event}\n"
        if id:
            message += f"id: {id}\n"
        if retry:
            message += f"retry: {retry}\n"
        
        # Handle multi-line data
        if isinstance(data, (dict, list)):
            data = json.dumps(data)
        
        for line in str(data).splitlines():
            message += f"data: {line}\n"
        
        message += "\n"  # Extra newline to signal end of message
        return message
    
    @staticmethod
    def comment(text: str) -> str:
        """Send a comment (ignored by clients, useful for keep-alive)"""
        return f": {text}\n\n"


async def check_client_disconnect(request: Request) -> bool:
    """Check if client has disconnected"""
    return await request.is_disconnected()


# Redirect root to static index.html
@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")


# Example 1: Basic streaming with heartbeat
@app.get("/stream/basic")
async def stream_basic(request: Request):
    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            count = 0
            while True:
                # Check if client disconnected
                if await check_client_disconnect(request):
                    logger.info("Client disconnected")
                    break
                
                count += 1
                data = {
                    "count": count,
                    "timestamp": datetime.now().isoformat(),
                    "message": f"Update #{count}"
                }
                
                yield SSEMessage.format(data, event="update", id=str(count))
                
                # Send heartbeat comment every 15 seconds to keep connection alive
                if count % 15 == 0:
                    yield SSEMessage.comment(f"heartbeat {datetime.now().isoformat()}")
                
                await asyncio.sleep(1)
                
                if count >= 30:
                    # Send completion event
                    yield SSEMessage.format(
                        {"status": "complete", "total": count},
                        event="done"
                    )
                    break
                    
        except asyncio.CancelledError:
            logger.info("Stream cancelled")
            raise
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield SSEMessage.format(
                {"error": str(e)},
                event="error"
            )
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


# Example 2: Simulated log streaming
@app.get("/stream/logs")
async def stream_logs(request: Request):
    async def log_generator() -> AsyncGenerator[str, None]:
        log_levels = ["INFO", "DEBUG", "WARNING", "ERROR"]
        messages = [
            "Application started",
            "Database connection established",
            "Processing request",
            "Cache miss, fetching from database",
            "Request completed successfully",
            "Cleaning up temporary files",
            "Background job queued",
            "Metrics collected",
        ]
        
        try:
            for i, message in enumerate(messages):
                if await check_client_disconnect(request):
                    break
                
                import random
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "level": random.choice(log_levels),
                    "message": message,
                    "line": i + 1
                }
                
                yield SSEMessage.format(log_entry, event="log", id=str(i))
                await asyncio.sleep(0.5)
            
            yield SSEMessage.format({"status": "EOF"}, event="complete")
            
        except asyncio.CancelledError:
            logger.info("Log stream cancelled")
            raise
    
    return StreamingResponse(
        log_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# Example 3: Progress tracking
@app.get("/stream/progress")
async def stream_progress(request: Request):
    async def progress_generator() -> AsyncGenerator[str, None]:
        steps = [
            "Initializing...",
            "Loading dependencies...",
            "Processing data...",
            "Running calculations...",
            "Generating report...",
            "Finalizing...",
            "Complete!"
        ]
        
        try:
            for i, step in enumerate(steps):
                if await check_client_disconnect(request):
                    break
                
                progress = {
                    "step": i + 1,
                    "total": len(steps),
                    "percentage": round((i + 1) / len(steps) * 100, 2),
                    "message": step,
                    "timestamp": datetime.now().isoformat()
                }
                
                yield SSEMessage.format(progress, event="progress", id=str(i))
                
                # Simulate work
                await asyncio.sleep(2)
            
        except asyncio.CancelledError:
            logger.info("Progress stream cancelled")
            raise
    
    return StreamingResponse(
        progress_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# Example 4: Multiple event types with error handling
@app.get("/stream/multi")
async def stream_multi_events(request: Request):
    async def multi_event_generator() -> AsyncGenerator[str, None]:
        try:
            # Send initial connection event
            yield SSEMessage.format(
                {"connected": True, "timestamp": datetime.now().isoformat()},
                event="connected",
                id="0"
            )
            
            for i in range(20):
                if await check_client_disconnect(request):
                    break
                
                # Send different types of events
                if i % 5 == 0:
                    # Status event
                    yield SSEMessage.format(
                        {"status": "healthy", "uptime": i},
                        event="status"
                    )
                elif i % 3 == 0:
                    # Metric event
                    import random
                    yield SSEMessage.format(
                        {
                            "cpu": random.uniform(0, 100),
                            "memory": random.uniform(0, 100),
                            "requests": random.randint(0, 1000)
                        },
                        event="metrics"
                    )
                else:
                    # Regular update
                    yield SSEMessage.format(
                        {"count": i, "message": f"Update {i}"},
                        event="update",
                        id=str(i)
                    )
                
                # Simulate an error condition
                if i == 10:
                    yield SSEMessage.format(
                        {"message": "Warning: High memory usage detected"},
                        event="warning"
                    )
                
                # Heartbeat comment
                if i % 5 == 0:
                    yield SSEMessage.comment("keep-alive")
                
                await asyncio.sleep(1)
            
            # Send final event
            yield SSEMessage.format(
                {"message": "Stream completed"},
                event="complete"
            )
            
        except asyncio.CancelledError:
            logger.info("Multi-event stream cancelled")
            yield SSEMessage.format(
                {"message": "Stream interrupted"},
                event="error"
            )
            raise
        except Exception as e:
            logger.error(f"Error in stream: {e}")
            yield SSEMessage.format(
                {"error": str(e)},
                event="error"
            )
    
    return StreamingResponse(
        multi_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# Example 5: Simulated chat/AI response streaming
@app.get("/stream/chat")
async def stream_chat(request: Request, message: str = "Hello, how are you?"):
    async def chat_generator() -> AsyncGenerator[str, None]:
        response = f"Thanks for asking '{message}'! Here's my response in chunks..."
        
        try:
            # Stream word by word
            words = response.split()
            for i, word in enumerate(words):
                if await check_client_disconnect(request):
                    break
                
                chunk = {
                    "chunk": word + " ",
                    "index": i,
                    "is_final": i == len(words) - 1
                }
                
                yield SSEMessage.format(chunk, event="chunk", id=str(i))
                await asyncio.sleep(0.1)
            
            # Send completion event
            yield SSEMessage.format(
                {
                    "content": response,
                    "tokens": len(words),
                    "completed_at": datetime.now().isoformat()
                },
                event="done"
            )
            
        except asyncio.CancelledError:
            logger.info("Chat stream cancelled")
            raise
    
    return StreamingResponse(
        chat_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)