"""
Orchestrator Agent - Routes tasks to appropriate specialist agents
"""

import os
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage


class OrchestratorAgent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.3,
            google_api_key=api_key,
        )
        
        self.system_prompt = """You are an orchestrator agent that routes user requests to the appropriate specialist.

Available specialists:
- math_specialist: Handles mathematical calculations, equations, statistics, and numerical problems

Your job is to:
1. Analyze the user's request
2. Determine if it requires the math specialist or if you can handle it directly
3. Respond with either:
   - "ROUTE_TO_MATH" if the request involves mathematical computation
   - A direct response if it's a general question

Examples:
- "What is 25 * 17?" → "ROUTE_TO_MATH"
- "Calculate the area of a circle with radius 5" → "ROUTE_TO_MATH"
- "Hello, how are you?" → Direct response
- "What's the weather like?" → Direct response

Be concise and accurate in your routing decisions."""

    def process(self, user_input: str) -> Dict[str, Any]:
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_input)
        ]
        
        response = self.llm.invoke(messages)
        
        if "ROUTE_TO_MATH" in response.content:
            return {
                "action": "route",
                "specialist": "math_specialist",
                "original_query": user_input
            }
        else:
            return {
                "action": "respond",
                "response": response.content
            }