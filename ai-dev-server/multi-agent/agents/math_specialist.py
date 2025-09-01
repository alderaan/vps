"""
Math Specialist Agent - Handles mathematical computations and problems
"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage


class MathSpecialistAgent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.1,  # Lower temperature for more precise math
            google_api_key=api_key,
        )
        
        self.system_prompt = """You are a specialized mathematics agent. You excel at:

- Arithmetic calculations (addition, subtraction, multiplication, division)
- Algebra and equations
- Geometry and trigonometry
- Statistics and probability
- Calculus operations
- Mathematical word problems

Always:
1. Show your work step-by-step
2. Double-check calculations
3. Provide clear, accurate answers
4. Use proper mathematical notation when helpful
5. Explain the reasoning behind your approach

If the problem seems ambiguous, ask for clarification.
If you need to make assumptions, state them clearly."""

    def process(self, math_query: str) -> str:
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"Solve this mathematical problem: {math_query}")
        ]
        
        response = self.llm.invoke(messages)
        return str(response.content)