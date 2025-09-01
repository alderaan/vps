#!/usr/bin/env python3
"""
Multi-Agent System with LangGraph
Demonstrates orchestrator routing requests to specialist agents
"""

import os
from workflow import MultiAgentWorkflow


def main():
    # Check API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        print("Please add 'export GEMINI_API_KEY=your-api-key' to your ~/.zshrc")
        return
    
    # Initialize workflow
    print("🚀 Initializing Multi-Agent System...")
    workflow = MultiAgentWorkflow()
    
    # Choose mode
    print("\nChoose mode:")
    print("1. Interactive mode (enter your own messages)")
    print("2. Demo mode (run test cases)")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        interactive_mode(workflow)
    else:
        demo_mode(workflow)

def interactive_mode(workflow):
    """Interactive mode for user input"""
    print("\n💬 Interactive Mode - Enter your messages (type 'quit' to exit)")
    print("="*70)
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        
        if not user_input:
            continue
            
        try:
            response = workflow.run(user_input)
        except Exception as e:
            print(f"❌ Error: {e}")

def demo_mode(workflow):
    """Demo mode with test cases"""
    test_queries = [
        "Hello! How are you today?",
        "What is 25 * 17 + 100?",
        "Calculate the area of a circle with radius 8",
        "What's the capital of France?",
        "Solve for x: 2x + 5 = 17"
    ]
    
    print("\n🧪 Running test queries...\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Test {i} ---")
        try:
            response = workflow.run(query)
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n" + "="*70)
    
    print("\n✨ Multi-agent system demo complete!")


if __name__ == "__main__":
    main()