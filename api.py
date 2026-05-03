"""
Finai Agent FastAPI Service
REST API wrapper for Finai personal finance advisor AI agent
"""

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Finai Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict di production
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """Request model untuk chat endpoint"""
    message: str
    conversation_history: List[Dict[str, Any]] = []
    user_token: str              # JWT token dari kayakaga-api
    user_context: Dict[str, Any] = {}      # profile + accounts untuk system prompt


class ChatResponse(BaseModel):
    """Response model untuk chat endpoint"""
    reply: str
    conversation_history: List[Dict[str, Any]]
    tools_called: List[Dict[str, Any]] = []


class ResetResponse(BaseModel):
    """Response model untuk reset endpoint"""
    success: bool
    message: str


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "finai-agent-api"}


@app.post("/agent/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Process chat message dari user.

    user_token dipakai untuk tools call ke kayakaga-api.
    user_context dipakai untuk build system prompt dengan profile & accounts user.
    """
    try:
        from agent.brain import run_agent
        from agent.prompts import build_system_prompt

        # Build system prompt dari user_context yang dikirim
        system_prompt = build_system_prompt(request.user_context)

        # Track tools yang dipanggil
        tools_called = []

        reply, updated_history = run_agent(
            user_message=request.message,
            conversation_history=request.conversation_history,
            system_prompt=system_prompt,
            user_token=request.user_token,
            tools_called_tracker=tools_called
        )

        return ChatResponse(
            reply=reply,
            conversation_history=updated_history,
            tools_called=tools_called
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/agent/chat/reset")
def reset_chat():
    """Reset conversation — client handle history, ini hanya acknowledgment."""
    return ResetResponse(success=True, message="Conversation reset")


if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host=os.getenv("AGENT_HOST", "0.0.0.0"),
        port=int(os.getenv("AGENT_PORT", 8000)),
        reload=os.getenv("APP_ENV") == "development"
    )
