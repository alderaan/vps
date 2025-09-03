"""
LangGraph Multi-Agent Workflow
Orchestrates communication between orchestrator and specialist agents
"""

from typing import Dict, Any, List
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from agents.orchestrator import OrchestratorAgent
from agents.math_specialist import MathSpecialistAgent


class AgentState(TypedDict):
    """State passed between agents in the workflow"""
    user_input: str
    messages: List[str]
    current_agent: str
    final_response: str


class MultiAgentWorkflow:
    def __init__(self):
        self.orchestrator = OrchestratorAgent()
        self.math_specialist = MathSpecialistAgent()
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("orchestrator", self._orchestrator_node)
        workflow.add_node("math_specialist", self._math_specialist_node)
        workflow.add_node("final_response", self._final_response_node)
        
        # Define the flow
        workflow.set_entry_point("orchestrator")
        
        # Conditional routing from orchestrator
        workflow.add_conditional_edges(
            "orchestrator",
            self._should_route_to_specialist,
            {
                "math_specialist": "math_specialist",
                "end": "final_response"
            }
        )
        
        # Math specialist always goes to final response
        workflow.add_edge("math_specialist", "final_response")
        workflow.add_edge("final_response", END)
        
        return workflow.compile()
    
    def _orchestrator_node(self, state: AgentState) -> AgentState:
        """Process request through orchestrator"""
        print("🧠 Orchestrator: Analyzing request...")
        
        result = self.orchestrator.process(state["user_input"])
        
        state["messages"].append(f"Orchestrator decision: {result}")
        state["current_agent"] = "orchestrator"
        
        if result["action"] == "respond":
            state["final_response"] = result["response"]
        
        return state
    
    def _math_specialist_node(self, state: AgentState) -> AgentState:
        """Process math request through specialist"""
        print("🔢 Math Specialist: Solving problem...")
        
        response = self.math_specialist.process(state["user_input"])
        
        state["messages"].append(f"Math specialist response: {response}")
        state["current_agent"] = "math_specialist"
        state["final_response"] = response
        
        return state
    
    def _final_response_node(self, state: AgentState) -> AgentState:
        """Prepare final response"""
        print("✅ Finalizing response...")
        return state
    
    def _should_route_to_specialist(self, state: AgentState) -> str:
        """Determine if we should route to a specialist"""
        # Check if orchestrator decided to route
        last_message = state["messages"][-1] if state["messages"] else ""
        
        if "math_specialist" in last_message:
            return "math_specialist"
        else:
            return "end"
    
    def run(self, user_input: str) -> str:
        """Run the multi-agent workflow"""
        # Truncate long inputs for logging (keep first 100 chars)
        display_input = user_input[:100] + "..." if len(user_input) > 100 else user_input
        print(f"💬 User: {display_input}")
        print("=" * 50)
        
        # Initialize state
        initial_state = AgentState(
            user_input=user_input,
            messages=[],
            current_agent="",
            final_response=""
        )
        
        # Execute workflow
        final_state = self.workflow.invoke(initial_state)
        
        print("=" * 50)
        # Truncate long responses for logging
        display_response = final_state['final_response'][:200] + "..." if len(final_state['final_response']) > 200 else final_state['final_response']
        print(f"🤖 Final Response: {display_response}")
        
        return final_state['final_response']