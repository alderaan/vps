"""
OpenAI-Compatible Endpoint for 11Labs Integration
Routes requests to the multi-agent LangGraph system
"""

import os
import sys
from pathlib import Path
from typing import Optional, AsyncGenerator
from fastapi import HTTPException, Header, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
import logging
import json
import uuid
import time

# Add multi-agent directory to path
sys.path.append(str(Path(__file__).parent / "multi-agent"))

from multi_agent_models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    Choice,
    Usage,
    ErrorResponse
)

logger = logging.getLogger(__name__)

# Security scheme for OpenAPI docs
security = HTTPBearer()

# Get API key from environment
MULTI_AGENT_API_KEY = os.getenv("MULTI_AGENT_API_KEY")
if not MULTI_AGENT_API_KEY:
    logger.warning("MULTI_AGENT_API_KEY not set - using default for development")
    MULTI_AGENT_API_KEY = "sk-dev-test-key"  # Default for development


class MultiAgentAdapter:
    """Adapter to connect OpenAI requests to multi-agent system"""
    
    def __init__(self):
        self.workflow = None
        self._initialize_workflow()
    
    def _initialize_workflow(self):
        """Lazy initialization of workflow to avoid import issues"""
        try:
            # Import here to avoid circular dependencies
            from workflow import MultiAgentWorkflow
            self.workflow = MultiAgentWorkflow()
            logger.info("Multi-agent workflow initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize multi-agent workflow: {e}")
            self.workflow = None
    
    async def process_chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Process chat completion request through multi-agent system"""
        
        if not self.workflow:
            self._initialize_workflow()
            if not self.workflow:
                raise HTTPException(
                    status_code=503,
                    detail="Multi-agent system not available"
                )
        
        try:
            # Extract the last user message (most recent query)
            user_message = None
            system_message = None
            
            for msg in request.messages:
                if msg.role == "user":
                    user_message = msg.content
                elif msg.role == "system":
                    system_message = msg.content
            
            if not user_message:
                raise ValueError("No user message found in request")
            
            # Prepend system message if provided
            if system_message:
                user_message = f"{system_message}\n\n{user_message}"
            
            # Process through multi-agent workflow
            response_text = self.workflow.run(user_message)
            
            # Create OpenAI-format response
            response = ChatCompletionResponse(
                model=request.model,
                choices=[
                    Choice(
                        index=0,
                        message=ChatMessage(
                            role="assistant",
                            content=response_text
                        ),
                        finish_reason="stop"
                    )
                ],
                usage=Usage(
                    prompt_tokens=len(user_message.split()),  # Rough estimate
                    completion_tokens=len(response_text.split()),  # Rough estimate
                    total_tokens=len(user_message.split()) + len(response_text.split())
                )
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing chat completion: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing request: {str(e)}"
            )


# Global adapter instance
adapter = MultiAgentAdapter()


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Verify the API key from Authorization header"""
    
    # Check if it's a Bearer token
    if credentials.scheme != "Bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication scheme. Use Bearer token."
        )
    
    # Validate the token
    token = credentials.credentials
    
    # Accept both formats: with or without 'sk-' prefix
    if token == MULTI_AGENT_API_KEY or f"sk-{token}" == MULTI_AGENT_API_KEY:
        return token
    
    raise HTTPException(
        status_code=401,
        detail="Invalid API key"
    )


async def stream_chat_completion(request: ChatCompletionRequest) -> AsyncGenerator[str, None]:
    """Generate streaming response in OpenAI format with buffer words support"""
    
    # Create a unique ID for this stream
    stream_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
    
    # Analyze the user's last message to determine if we need buffer words
    user_message = ""
    for msg in reversed(request.messages):
        if msg.role == "user":
            user_message = msg.content.lower()
            break
    
    # Determine appropriate buffer words based on query type
    buffer_phrase = None
    if any(word in user_message for word in ["calculate", "multiply", "divide", "plus", "minus", "times", "math", "what's", "what is"]):
        if any(op in user_message for op in ["times", "multiply", "*", "x"]):
            buffer_phrase = "Let me calculate that multiplication for you... "
        elif any(op in user_message for op in ["plus", "add", "+"]):
            buffer_phrase = "Let me add those numbers... "
        elif any(op in user_message for op in ["divide", "/"]):
            buffer_phrase = "Let me work out that division... "
        else:
            buffer_phrase = "Let me calculate that for you... "
    elif any(word in user_message for word in ["search", "find", "look", "check"]):
        buffer_phrase = "Let me search for that information... "
    elif any(word in user_message for word in ["help", "how", "what", "why", "when", "where"]):
        buffer_phrase = "Let me help you with that... "
    elif any(word in user_message for word in ["analyze", "review", "evaluate"]):
        buffer_phrase = "Let me analyze this for you... "
    
    # Send buffer words immediately if needed
    if buffer_phrase:
        buffer_chunk = {
            "id": stream_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "delta": {
                        "content": buffer_phrase
                    },
                    "finish_reason": None
                }
            ]
        }
        yield f"data: {json.dumps(buffer_chunk)}\n\n"
        logger.info(f"Sent buffer words: {buffer_phrase}")
    
    # Now process the actual response
    response = await adapter.process_chat_completion(request)
    full_content = response.choices[0].message.content
    
    # Split content into words for streaming
    words = full_content.split()
    
    # Stream each word with proper SSE format
    for i, word in enumerate(words):
        chunk = {
            "id": stream_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "delta": {
                        "content": word + (" " if i < len(words) - 1 else "")
                    },
                    "finish_reason": None
                }
            ]
        }
        yield f"data: {json.dumps(chunk)}\n\n"
    
    # Send final chunk with finish_reason
    final_chunk = {
        "id": stream_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }
        ]
    }
    yield f"data: {json.dumps(final_chunk)}\n\n"
    yield "data: [DONE]\n\n"


async def chat_completions_endpoint(
    request: ChatCompletionRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    OpenAI-compatible chat completions endpoint for 11Labs integration.
    
    Accepts standard OpenAI chat completion requests and routes them
    through the multi-agent LangGraph system.
    """
    
    # Handle streaming vs non-streaming
    if request.stream:
        logger.info("Streaming response requested")
        return StreamingResponse(
            stream_chat_completion(request),
            media_type="text/event-stream"
        )
    else:
        # Process non-streaming request
        response = await adapter.process_chat_completion(request)
        return response