#!/usr/bin/env python3
"""
LangChain Hello World with Gemini
Simple example using LangChain with Google's Gemini model
"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage


def main():
    # Get API key from environment variable
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        print("Please add 'export GEMINI_API_KEY=your-api-key' to your ~/.zshrc")
        return

    # Initialize Gemini model - using gemini-1.5-flash for fast responses
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.7,
        google_api_key=api_key,
    )

    # Create messages
    messages = [
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(
            content="Hello! This is a test of LangChain with Gemini. Can you respond with a simple greeting?"
        ),
    ]

    # Get response
    print("Sending message to Gemini...")
    response = llm.invoke(messages)

    print("\nGemini's response:")
    print(response.content)


if __name__ == "__main__":
    main()
