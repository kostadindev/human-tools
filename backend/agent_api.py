"""
Agent API Server
Multi-agent orchestration system with specialized AI agents and human-in-the-loop.
"""
import os
import uuid
import httpx
import threading
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.tools import tool
from langchain_core.prompts import PromptTemplate

load_dotenv()

app = FastAPI(title="Agent API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for pending callbacks
# query_id -> asyncio.Event and response data
pending_callbacks: dict = {}

# Task history storage
# agent_id -> List[TaskHistory]
task_history: Dict[str, List[Dict[str, Any]]] = {
    'agent-1': [],  # Analytical agent
    'agent-2': [],  # Creative agent
    'human': [],    # Human agent
}

# Initialize LLMs for different agents
orchestrator_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

agent_1_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.5,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

agent_2_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.9,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

print("🤖 Agents initialized with Gemini 2.5 Flash")


@tool
def query_human(question: str) -> str:
    """Ask a human for information. Use this when you need human input or clarification."""
    human_api_url = os.getenv("HUMAN_API_URL", "http://localhost:8001")
    agent_api_url = os.getenv("AGENT_API_URL", "http://localhost:8000")
    timeout_seconds = 300  # 5 minutes

    print(f"\n🔧 TOOL CALLED: query_human")
    print(f"   Question: {question}")

    try:
        # Step 1: Submit query to Human API with callback URL
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{human_api_url}/query",
                json={
                    "question": question,
                    "context": None,
                    "callback_url": f"{agent_api_url}/callback"
                }
            )
            response.raise_for_status()
            data = response.json()
            query_id = data["query_id"]

        print(f"   Query ID: {query_id}")
        print(f"   ⏳ Waiting for human response (via callback)...")

        # Step 2: Create threading event and wait for callback
        event = threading.Event()
        pending_callbacks[query_id] = {
            "event": event,
            "response": None
        }

        # Wait for callback with timeout
        received = event.wait(timeout=timeout_seconds)

        if not received:
            timeout_msg = f"Timeout: Human did not respond within {timeout_seconds} seconds"
            print(f"   ⏰ {timeout_msg}\n")
            pending_callbacks.pop(query_id, None)
            
            # Record timeout in history
            task_history['human'].append({
                'id': str(uuid.uuid4()),
                'timestamp': datetime.now().isoformat(),
                'action': f"Timeout waiting for response: {question[:80]}{'...' if len(question) > 80 else ''}",
                'status': 'error'
            })
            
            return timeout_msg

        # Get response
        result = pending_callbacks[query_id]["response"]
        pending_callbacks.pop(query_id, None)

        # Record task history for human
        task_history['human'].append({
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'action': f"Responded to query: {question[:80]}{'...' if len(question) > 80 else ''}",
            'status': 'success'
        })

        print(f"   ✅ Response received: {result}\n")
        return result

    except Exception as e:
        error_msg = f"Error querying human: {str(e)}"
        print(f"   ❌ Error: {error_msg}\n")
        pending_callbacks.pop(query_id, None) if 'query_id' in locals() else None
        return error_msg


@tool
def analytical_agent(task: str) -> str:
    """
    An analytical AI agent specialized in logical reasoning, data analysis, and structured thinking.
    Use this agent for tasks requiring: analysis, comparison, evaluation, or logical problem-solving.
    """
    print(f"\n🔬 TOOL CALLED: analytical_agent")
    print(f"   Task: {task}")

    try:
        prompt = f"""You are an analytical AI agent specialized in logical reasoning and structured thinking.

Task: {task}

Provide a well-reasoned, analytical response. Focus on:
- Breaking down complex problems
- Logical step-by-step reasoning
- Data-driven insights
- Structured conclusions

Response:"""

        response = agent_1_llm.invoke(prompt)
        result = response.content
        
        # Record task history
        history_entry = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'action': task[:100] + ('...' if len(task) > 100 else ''),  # Truncate long tasks
            'status': 'success'
        }
        task_history['agent-1'].append(history_entry)
        print(f"   📝 History recorded: {len(task_history['agent-1'])} total tasks\n")
        
        print(f"   ✅ Analytical agent completed\n")
        return result
    except Exception as e:
        error_msg = f"Error in analytical agent: {str(e)}"
        
        # Record failed task
        history_entry = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'action': task[:100] + ('...' if len(task) > 100 else ''),
            'status': 'error'
        }
        task_history['agent-1'].append(history_entry)
        print(f"   📝 Error history recorded: {len(task_history['agent-1'])} total tasks\n")
        
        print(f"   ❌ Error: {error_msg}\n")
        return error_msg


@tool
def creative_agent(task: str) -> str:
    """
    A creative AI agent specialized in brainstorming, ideation, and creative problem-solving.
    Use this agent for tasks requiring: creativity, idea generation, storytelling, or innovative solutions.
    """
    print(f"\n🎨 TOOL CALLED: creative_agent")
    print(f"   Task: {task}")

    try:
        prompt = f"""You are a creative AI agent specialized in brainstorming and innovative thinking.

Task: {task}

Provide a creative, innovative response. Focus on:
- Out-of-the-box thinking
- Creative solutions and ideas
- Multiple perspectives
- Imaginative approaches

Response:"""

        response = agent_2_llm.invoke(prompt)
        result = response.content
        
        # Record task history
        history_entry = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'action': task[:100] + ('...' if len(task) > 100 else ''),  # Truncate long tasks
            'status': 'success'
        }
        task_history['agent-2'].append(history_entry)
        print(f"   📝 History recorded: {len(task_history['agent-2'])} total tasks\n")
        
        print(f"   ✅ Creative agent completed\n")
        return result
    except Exception as e:
        error_msg = f"Error in creative agent: {str(e)}"
        
        # Record failed task
        history_entry = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'action': task[:100] + ('...' if len(task) > 100 else ''),
            'status': 'error'
        }
        task_history['agent-2'].append(history_entry)
        print(f"   📝 Error history recorded: {len(task_history['agent-2'])} total tasks\n")
        
        print(f"   ❌ Error: {error_msg}\n")
        return error_msg


# All available tools
ALL_TOOLS = {
    'agent': [analytical_agent, creative_agent],
    'human': [query_human],
}

# Map node types to tool names
TOOL_MAP = {
    'agent': ['analytical_agent', 'creative_agent'],
    'human': ['query_human'],
}


def get_tools_from_diagram(diagram: Optional[DiagramStructure]) -> List:
    """
    Parse diagram structure and return only the tools that the orchestrator is connected to.
    This enforces the diagram architecture.
    """
    if not diagram:
        # If no diagram provided, use all tools (backward compatibility)
        return [analytical_agent, creative_agent, query_human]

    # Find orchestrator node
    orchestrator_id = None
    for node in diagram.nodes:
        if node.type == 'orchestrator':
            orchestrator_id = node.id
            break

    if not orchestrator_id:
        print("⚠️  No orchestrator found in diagram, using all tools")
        return [analytical_agent, creative_agent, query_human]

    # Find what the orchestrator is connected to
    connected_node_ids = set()
    for edge in diagram.edges:
        if edge.source == orchestrator_id:
            connected_node_ids.add(edge.target)

    # Map connected nodes to tools
    available_tools = []
    tool_names = []

    for node in diagram.nodes:
        if node.id in connected_node_ids:
            if node.type == 'agent':
                available_tools.extend([analytical_agent, creative_agent])
                tool_names.extend(['analytical_agent', 'creative_agent'])
            elif node.type == 'human':
                available_tools.append(query_human)
                tool_names.append('query_human')

    # Remove duplicates while preserving order
    seen = set()
    unique_tools = []
    for tool in available_tools:
        if tool.name not in seen:
            seen.add(tool.name)
            unique_tools.append(tool)

    if not unique_tools:
        print("⚠️  No tools connected in diagram, using all tools as fallback")
        return [analytical_agent, creative_agent, query_human]

    print(f"🔧 Tools enabled from diagram: {[t.name for t in unique_tools]}")
    return unique_tools


# Default tools (will be overridden by diagram)
tools = [analytical_agent, creative_agent, query_human]

# Orchestrator prompt template
template = """You are an orchestrator agent coordinating a team of specialized agents and a human collaborator.

AVAILABLE TOOLS - You can ONLY use these tools (no others):

{tools}

Your available tools are ONLY: [{tool_names}]

Tool Descriptions:
- analytical_agent: Use for tasks requiring logical reasoning, data analysis, evaluation, or structured thinking
- creative_agent: Use for tasks requiring brainstorming, ideation, storytelling, or innovative solutions
- query_human: Use when you need human judgment, preferences, approval, or information only a human would know

CRITICAL RULES:
1. ONLY use tools from [{tool_names}] - no other tools exist for you
2. If the user asks you to use a tool that is NOT in your available tools list:
   - Simply state: "I cannot do that because [tool_name] is not available in the current configuration."
   - List what tools you DO have available: [{tool_names}]
   - Do NOT try to work around it or use the unavailable tool
   - Provide your Final Answer immediately explaining the limitation
3. If you can answer the user's question directly without any tools, do so
4. You can use multiple available tools in sequence if needed
5. After getting responses from tools, synthesize them into a complete answer
6. ALWAYS provide a Final Answer - never leave without responding

Use the following format:

Question: the input question you must answer
Thought: think about what approach to take (direct answer or which available tool(s) to use)
Action: the action to take, MUST be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer synthesized from all information gathered

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

prompt = PromptTemplate.from_template(template)

print("✅ Orchestrator system initialized\n")


class Message(BaseModel):
    role: str
    content: str


class DiagramNode(BaseModel):
    id: str
    type: str
    label: str


class DiagramEdge(BaseModel):
    id: str
    source: str
    target: str


class DiagramStructure(BaseModel):
    nodes: List[DiagramNode]
    edges: List[DiagramEdge]


class ChatRequest(BaseModel):
    history: List[Message]
    diagram: Optional[DiagramStructure] = None


class SuggestionResponse(BaseModel):
    suggestions: List[str]


async def generate_streaming_response(history: List[Message], diagram: Optional[DiagramStructure] = None):
    """Stream orchestrator agent response to frontend"""
    try:
        # Get the last user message
        last_user_message = ""
        for msg in history:
            if msg.role == "user":
                last_user_message = msg.content

        print(f"\n💬 User: {last_user_message}")

        # Get tools based on diagram structure (ENFORCES DIAGRAM)
        active_tools = get_tools_from_diagram(diagram)
        active_tool_names = {tool.name for tool in active_tools}

        if diagram:
            # Find orchestrator and what it's connected to
            orchestrator_id = None
            for node in diagram.nodes:
                if node.type == 'orchestrator':
                    orchestrator_id = node.id
                    break

            connected_labels = []
            if orchestrator_id:
                connected_ids = {edge.target for edge in diagram.edges if edge.source == orchestrator_id}
                connected_labels = [node.label for node in diagram.nodes if node.id in connected_ids]

            print(f"📊 Diagram: {len(diagram.nodes)} nodes, {len(diagram.edges)} edges")
            print(f"   Orchestrator ACTUALLY connected to: {connected_labels}")
            print(f"   Available tools: {list(active_tool_names)}")

        # Create dynamic agent executor with diagram-filtered tools
        orchestrator_agent = create_react_agent(orchestrator_llm, active_tools, prompt)
        executor = AgentExecutor(
            agent=orchestrator_agent,
            tools=active_tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=15,
            early_stopping_method="force"
        )

        # Track tool calls - ONLY for available tools
        all_tool_messages = {
            "query_human": "🤔 Asking human for help... please wait for their response.",
            "analytical_agent": "🔬 Consulting analytical agent...",
            "creative_agent": "🎨 Consulting creative agent..."
        }
        # Filter to only show messages for available tools
        tool_messages = {
            tool_name: msg
            for tool_name, msg in all_tool_messages.items()
            if tool_name in active_tool_names
        }
        shown_tool_messages = set()

        # Run orchestrator and stream response
        response_generated = False
        async for chunk in executor.astream({"input": last_user_message}):
            # Stream tool actions (when orchestrator decides to use a tool)
            if "actions" in chunk:
                for action in chunk["actions"]:
                    # Validate tool is available
                    if action.tool not in active_tool_names:
                        print(f"⚠️  Agent tried to use unavailable tool: {action.tool}")
                        continue

                    if action.tool in tool_messages and action.tool not in shown_tool_messages:
                        yield tool_messages[action.tool]
                        shown_tool_messages.add(action.tool)

            # When tool completes
            if "steps" in chunk:
                for step in chunk["steps"]:
                    tool_name = step.action.tool
                    if tool_name in shown_tool_messages:
                        yield "\n\n✅ Response received! Processing...\n\n"

            # Stream final output
            if "output" in chunk:
                yield chunk["output"]
                response_generated = True

        # If no response was generated, provide a helpful fallback
        if not response_generated:
            fallback_msg = "I apologize, but I'm having difficulty processing your request. "
            if diagram and active_tools:
                available_names = [t.name.replace('_', ' ') for t in active_tools]
                fallback_msg += f"I currently have access to: {', '.join(available_names)}. "
            fallback_msg += "Could you please rephrase your question?"
            yield fallback_msg

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"❌ {error_msg}")
        # Provide a user-friendly error message
        yield f"I encountered an error while processing your request. "
        if "No generation chunks" in str(e) or "Invalid Format" in str(e):
            yield f"My available capabilities are: {', '.join([t.name.replace('_', ' ') for t in active_tools])}. "
            yield f"Could you please rephrase your question to align with these capabilities?"
        else:
            yield f"Error details: {error_msg}"


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat with the orchestrator agent. The orchestrator coordinates specialized AI agents and human collaboration.
    Streams the response back to the client.
    Each request is handled independently and won't block other requests.
    """
    request_id = str(uuid.uuid4())[:8]
    print(f"\n🆕 New chat request: {request_id}")

    return StreamingResponse(
        generate_streaming_response(request.history, request.diagram),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "X-Request-ID": request_id
        }
    )


@app.post("/suggest-followups", response_model=SuggestionResponse)
async def suggest_followups(request: ChatRequest):
    """
    Generate follow-up question suggestions based on conversation history.
    """
    # Simple implementation - could be enhanced with LLM-generated suggestions
    suggestions = [
        "Can you elaborate on that?",
        "Tell me more",
        "What else should I know?",
    ]
    return SuggestionResponse(suggestions=suggestions)


class CallbackRequest(BaseModel):
    query_id: str
    response: str


@app.post("/callback")
async def receive_callback(callback: CallbackRequest):
    """
    Callback endpoint for Human API to send responses.
    Wakes up the waiting query_human tool.
    """
    query_id = callback.query_id
    response = callback.response

    print(f"\n📞 CALLBACK RECEIVED")
    print(f"   Query ID: {query_id}")
    print(f"   Response: {response}\n")

    if query_id in pending_callbacks:
        # Store response and set event to wake up waiting tool
        pending_callbacks[query_id]["response"] = response
        pending_callbacks[query_id]["event"].set()
        return {"message": "Callback received successfully"}
    else:
        print(f"   ⚠️  Warning: Query ID not found in pending callbacks")
        return {"message": "Query ID not found or already completed"}


@app.get("/ping")
async def ping():
    """Ping endpoint to wake up the server"""
    return {"status": "ok"}


@app.get("/agent/{agent_id}/history")
async def get_agent_history(agent_id: str):
    """
    Get task history for a specific agent or human.
    Supported agent_ids: 'agent-1', 'agent-2', 'human'
    """
    print(f"\n📊 History request for: {agent_id}")
    print(f"   Available agents in history: {list(task_history.keys())}")
    
    if agent_id not in task_history:
        print(f"   ⚠️  Agent {agent_id} not found, returning empty history")
        return {"history": []}
    
    # Return history in reverse chronological order (newest first)
    history = task_history[agent_id].copy()
    history.reverse()
    print(f"   ✅ Returning {len(history)} history entries")
    return {"history": history}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "agent-api"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("AGENT_API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
