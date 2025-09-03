#!/usr/bin/env python3
"""
Test script for OpenAI-compatible endpoint
"""

import httpx
import json
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "http://localhost:8080"
API_KEY = os.getenv("MULTI_AGENT_API_KEY", "sk-dev-test-key")


async def test_chat_completion():
    """Test the chat completions endpoint"""
    
    # Test cases
    test_messages = [
        {
            "name": "General Greeting",
            "messages": [
                {"role": "user", "content": "Hello! How are you?"}
            ]
        },
        {
            "name": "Math Problem",
            "messages": [
                {"role": "user", "content": "What is 15 * 23 + 100?"}
            ]
        },
        {
            "name": "With System Message",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Calculate the area of a circle with radius 10"}
            ]
        }
    ]
    
    async with httpx.AsyncClient() as client:
        for test in test_messages:
            print(f"\n{'='*60}")
            print(f"Test: {test['name']}")
            print(f"{'='*60}")
            
            # Prepare request
            request_data = {
                "model": "multi-agent-system",
                "messages": test["messages"],
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            print(f"Request: {json.dumps(request_data, indent=2)}")
            
            try:
                # Make request
                response = await client.post(
                    f"{BASE_URL}/v1/chat/completions",
                    json=request_data,
                    headers={
                        "Authorization": f"Bearer {API_KEY}",
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"\n✅ Success!")
                    print(f"Response ID: {result.get('id')}")
                    print(f"Model: {result.get('model')}")
                    
                    # Extract the assistant's message
                    if result.get('choices'):
                        content = result['choices'][0]['message']['content']
                        print(f"\nAssistant: {content}")
                    
                    # Show token usage if available
                    if result.get('usage'):
                        usage = result['usage']
                        print(f"\nTokens - Prompt: {usage['prompt_tokens']}, "
                              f"Completion: {usage['completion_tokens']}, "
                              f"Total: {usage['total_tokens']}")
                else:
                    print(f"\n❌ Error: {response.status_code}")
                    print(f"Response: {response.text}")
                    
            except Exception as e:
                print(f"\n❌ Exception: {e}")


async def test_authentication():
    """Test authentication"""
    print("\n" + "="*60)
    print("Testing Authentication")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        # Test with invalid key
        print("\n1. Testing with invalid API key...")
        response = await client.post(
            f"{BASE_URL}/v1/chat/completions",
            json={
                "model": "test",
                "messages": [{"role": "user", "content": "test"}]
            },
            headers={
                "Authorization": "Bearer invalid-key",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 401:
            print("✅ Correctly rejected invalid key")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
        
        # Test without auth header
        print("\n2. Testing without Authorization header...")
        response = await client.post(
            f"{BASE_URL}/v1/chat/completions",
            json={
                "model": "test",
                "messages": [{"role": "user", "content": "test"}]
            },
            headers={
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 401 or response.status_code == 422:
            print("✅ Correctly rejected missing auth")
        else:
            print(f"❌ Unexpected response: {response.status_code}")


async def main():
    print("🚀 Testing OpenAI-Compatible Endpoint")
    print("="*60)
    print(f"Server: {BASE_URL}")
    print(f"API Key: {API_KEY[:10]}...")
    
    # Test authentication first
    await test_authentication()
    
    # Test chat completions
    await test_chat_completion()
    
    print("\n" + "="*60)
    print("✨ Tests complete!")


if __name__ == "__main__":
    asyncio.run(main())