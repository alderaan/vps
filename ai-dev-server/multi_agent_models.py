"""
OpenAI API Compatible Models for 11Labs Integration
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
import time
import uuid


# Request Models
class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = Field(default="multi-agent-system")
    messages: List[ChatMessage]
    temperature: Optional[float] = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=1000)
    stream: Optional[bool] = Field(default=False)
    n: Optional[int] = Field(default=1, ge=1)
    stop: Optional[List[str]] = None
    presence_penalty: Optional[float] = Field(default=0, ge=-2, le=2)
    frequency_penalty: Optional[float] = Field(default=0, ge=-2, le=2)
    user: Optional[str] = None


# Response Models
class Choice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Literal["stop", "length", "content_filter", "null"]


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:8]}")
    object: Literal["chat.completion"] = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[Choice]
    usage: Optional[Usage] = None
    system_fingerprint: Optional[str] = None


# Error Response Model
class ErrorResponse(BaseModel):
    error: Dict[str, Any]
    
    @classmethod
    def create(cls, message: str, type: str = "invalid_request_error", code: Optional[str] = None):
        return cls(
            error={
                "message": message,
                "type": type,
                "param": None,
                "code": code
            }
        )