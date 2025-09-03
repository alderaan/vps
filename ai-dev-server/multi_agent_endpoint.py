"""
OpenAI-Compatible Endpoint for 11Labs Integration
Routes requests to the multi-agent LangGraph system
"""

import os
import sys
from pathlib import Path
from typing import Optional
from fastapi import HTTPException, Header, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

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


async def chat_completions_endpoint(
    request: ChatCompletionRequest,
    api_key: str = Depends(verify_api_key)
) -> ChatCompletionResponse:
    """
    OpenAI-compatible chat completions endpoint for 11Labs integration.
    
    Accepts standard OpenAI chat completion requests and routes them
    through the multi-agent LangGraph system.
    """
    
    # Check if streaming is requested (not supported yet)
    if request.stream:
        raise HTTPException(
            status_code=501,
            detail="Streaming not yet implemented"
        )
    
    # Process the request
    response = await adapter.process_chat_completion(request)
    
    return response