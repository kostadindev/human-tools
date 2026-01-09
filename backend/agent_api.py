"""
Agent API Server
Multi-agent orchestration system with specialized AI agents and human-in-the-loop.
"""
from __future__ import annotations
import os
import uuid
import httpx
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.tools import tool
from langchain_core.prompts import PromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel

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
    'human': [],    # Human agent
}

# Determine which API provider to use (OpenAI takes precedence)
openai_api_key = os.getenv("OPENAI_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")

if openai_api_key:
    # Use OpenAI if API key is provided
    provider = "OpenAI"
    model_name = "gpt-4o-mini"
    
    orchestrator_llm: BaseChatModel = ChatOpenAI(
        model=model_name,
        temperature=0.7,
        openai_api_key=openai_api_key
    )
    
    agent_1_llm: BaseChatModel = ChatOpenAI(
        model=model_name,
        temperature=0.5,
        openai_api_key=openai_api_key
    )
    
    print(f"🤖 Agents initialized with {provider} ({model_name})")
elif google_api_key:
    # Fall back to Gemini if OpenAI key is not provided
    provider = "Gemini"
    model_name = "gemini-2.5-flash"
    
    orchestrator_llm: BaseChatModel = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0.7,
        google_api_key=google_api_key
    )
    
    agent_1_llm: BaseChatModel = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0.5,
        google_api_key=google_api_key
    )
    
    print(f"🤖 Agents initialized with {provider} ({model_name})")
else:
    raise ValueError(
        "No API key provided. Please set either OPENAI_API_KEY or GOOGLE_API_KEY in your .env file."
    )


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


# All available tools
ALL_TOOLS = {
    'agent': [analytical_agent],
    'human': [query_human],
}

# Map node types to tool names
TOOL_MAP = {
    'agent': ['analytical_agent'],
    'human': ['query_human'],
}


def get_tools_from_diagram(diagram: Optional[DiagramStructure]) -> List:
    """
    Parse diagram structure and return only the tools that the orchestrator is connected to.
    This enforces the diagram architecture.
    """
    if not diagram:
        # If no diagram provided, use all tools (backward compatibility)
        return [analytical_agent, query_human]

    # Find orchestrator node
    orchestrator_id = None
    for node in diagram.nodes:
        if node.type == 'orchestrator':
            orchestrator_id = node.id
            break

    if not orchestrator_id:
        print("⚠️  No orchestrator found in diagram, using all tools")
        return [analytical_agent, query_human]

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
                available_tools.append(analytical_agent)
                tool_names.append('analytical_agent')
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
        return [analytical_agent, query_human]

    print(f"🔧 Tools enabled from diagram: {[t.name for t in unique_tools]}")
    return unique_tools


# Default tools (will be overridden by diagram)
tools = [analytical_agent, query_human]


def load_constitution(constitution_file: Optional[str] = None, enabled: bool = True) -> str:
    """
    Load constitution text from file.
    Defaults to cambridge_university_v1.txt if no file specified.
    
    Args:
        constitution_file: Name of the constitution file to load
        enabled: Whether to load the constitution (if False, returns empty string)
    """
    if not enabled:
        print("📋 Constitution disabled (USE_CONSTITUTION=false)")
        return ""
    
    if constitution_file is None:
        constitution_file = os.getenv("CONSTITUTION_FILE", "cambridge_university_v1.txt")
    
    constitutions_dir = Path(__file__).parent / "constitutions"
    constitution_path = constitutions_dir / constitution_file
    
    if not constitution_path.exists():
        print(f"⚠️  Constitution file not found: {constitution_path}")
        print(f"   Using default empty constitution")
        return ""
    
    try:
        with open(constitution_path, 'r', encoding='utf-8') as f:
            constitution_text = f.read()
        print(f"✅ Loaded constitution from: {constitution_path}")
        return constitution_text
    except Exception as e:
        print(f"❌ Error loading constitution: {e}")
        return ""


# ============================================================================
# CONSTITUTION CONFIGURATION
# ============================================================================
# Set this to True to enable the constitution, False to disable it
# You can also override via USE_CONSTITUTION environment variable
# ============================================================================
USE_CONSTITUTION = False  # <-- Change this to False to disable constitution

# Load constitution at startup
# Priority: 1) CONSTITUTION_ENABLED variable, 2) USE_CONSTITUTION env var, 3) default True
env_override = os.getenv("USE_CONSTITUTION")

CONSTITUTION_TEXT = load_constitution(enabled=USE_CONSTITUTION)

# Debug output
print(f"🔧 Constitution configuration:")
print(f"   CONSTITUTION_ENABLED (code variable): {USE_CONSTITUTION}")
print(f"   USE_CONSTITUTION env var: {os.getenv('USE_CONSTITUTION', 'not set')}")
print(f"   Final USE_CONSTITUTION value: {USE_CONSTITUTION}")
print(f"   CONSTITUTION_TEXT loaded: {len(CONSTITUTION_TEXT) if CONSTITUTION_TEXT else 0} characters")


# Orchestrator prompt template
template = """You are an orchestrator agent that coordinates specialized AI agents and human collaborators to fulfill user requests.

YOUR ROLE:
- Evaluate user requests and determine the appropriate response strategy
- Select and invoke available tools (agents or human) to accomplish tasks
- Synthesize responses from tools into coherent final answers
- Apply any required stylization or formatting based on the constitution

AVAILABLE TOOLS - You can ONLY use these tools (no others):

{tools}

Your available tools are ONLY: [{tool_names}]

Tool Descriptions:
- analytical_agent: An AI agent that performs logical reasoning, data analysis, evaluation, and structured thinking
- query_human: A tool to request human input, judgment, or handoff when human oversight is needed

HOW TO OPERATE:

1. **Request Evaluation**: 
   - Read and understand the user's request
   - Evaluate the request against the constitution rules (if provided)
   - Determine if the request can be fulfilled, should be refused, or requires human handoff
   - If the request should be refused: Provide a refusal response based on constitution rules
   - If the request should be fulfilled: Proceed to tool selection
   - If the request requires human oversight based on the policies in the constitution or inability of the agents to fulfill the request: Use query_human tool

2. **Tool Selection**:
   - If the request can be fulfilled: Select the appropriate agent tool(s) to accomplish the task
   - If the request requires human oversight: Use query_human tool
   - If the request should be refused: Provide a refusal response based on constitution rules

3. **Response Processing**:
   - Invoke selected tools with appropriate inputs
   - Receive responses from tools
   - Apply any required stylization or formatting as specified in the constitution
   - Synthesize tool responses into a coherent final answer

4. **Tool Limitations**:
   - ONLY use tools from [{tool_names}] - no other tools exist
   - If a requested tool is not available, explain the limitation and list available tools
   - Do not attempt to work around unavailable tools

5. **Response Format**:
   - Always provide a Final Answer after processing
   - Return response in accordance and stylization with the constitution
   - If uncertain about constitution compliance, default to query_human rather than proceeding

Use the following format:

Question: the input question you must answer
Thought: think about what approach to take (evaluate against constitution, select tools, or provide direct answer)
Action: the action to take, MUST be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer synthesized from all information gathered

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

def create_orchestrator_prompt(constitution_text: str = "") -> PromptTemplate:
    """Create orchestrator prompt with constitution included."""
    constitution_section = ""
    if constitution_text and constitution_text.strip():
        constitution_section = f"""CONSTITUTION (You MUST abide by these rules):

{constitution_text}

---
"""
    
    full_template = constitution_section + template
    try:
        return PromptTemplate.from_template(full_template)
    except Exception as e:
        print(f"❌ Error creating prompt template: {e}")
        print(f"   Constitution enabled: {bool(constitution_text)}")
        print(f"   Template length: {len(full_template)}")
        raise

# Initialize prompt with constitution (respects USE_CONSTITUTION flag)
try:
    prompt = create_orchestrator_prompt(CONSTITUTION_TEXT if USE_CONSTITUTION else "")
    if USE_CONSTITUTION:
        print("✅ Orchestrator system initialized with constitution enabled\n")
    else:
        print("✅ Orchestrator system initialized without constitution (comparison mode)\n")
except Exception as e:
    print(f"❌ Failed to initialize orchestrator prompt: {e}")
    print(f"   Attempting to initialize without constitution...")
    try:
        prompt = create_orchestrator_prompt("")
        print("✅ Orchestrator system initialized without constitution (fallback mode)\n")
    except Exception as e2:
        print(f"❌ Critical error: Failed to initialize orchestrator even without constitution: {e2}")
        raise


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

        # Create dynamic agent executor with diagram-filtered tools and constitution-aware prompt
        # Recreate prompt with current constitution (respects USE_CONSTITUTION flag)
        current_prompt = create_orchestrator_prompt(CONSTITUTION_TEXT if USE_CONSTITUTION else "")
        orchestrator_agent = create_react_agent(orchestrator_llm, active_tools, current_prompt)
        executor = AgentExecutor(
            agent=orchestrator_agent,
            tools=active_tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=15,
            early_stopping_method="force"
        )

        # Run orchestrator and stream response
        response_generated = False
        async for chunk in executor.astream({"input": last_user_message}):
            # Validate tool is available (but don't show tool messages to user)
            if "actions" in chunk:
                for action in chunk["actions"]:
                    if action.tool not in active_tool_names:
                        print(f"⚠️  Agent tried to use unavailable tool: {action.tool}")
                        continue

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


class ConstitutionConfig(BaseModel):
    enabled: bool
    file_name: Optional[str] = None


@app.post("/constitution/config")
async def set_constitution_config(config: ConstitutionConfig):
    """
    Dynamically enable or disable the constitution and optionally set the file.
    WARNING: This modifies global state. Intended for testing purposes.
    """
    global USE_CONSTITUTION, CONSTITUTION_TEXT, prompt
    
    USE_CONSTITUTION = config.enabled
    
    # Reload constitution text based on new setting and optional file name
    CONSTITUTION_TEXT = load_constitution(
        constitution_file=config.file_name,
        enabled=USE_CONSTITUTION
    )
    
    # Re-initialize prompt
    try:
        prompt = create_orchestrator_prompt(CONSTITUTION_TEXT if USE_CONSTITUTION else "")
        status_msg = "enabled" if USE_CONSTITUTION else "disabled"
        print(f"\n🔧 Constitution dynamically {status_msg}")
        return {
            "message": f"Constitution {status_msg}",
            "enabled": USE_CONSTITUTION,
            "constitution_length": len(CONSTITUTION_TEXT)
        }
    except Exception as e:
        print(f"❌ Error updating constitution config: {e}")
        return {"error": str(e)}


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
    Supported agent_ids: 'agent-1', 'human'
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


@app.get("/constitution/status")
async def get_constitution_status():
    """
    Get the current constitution status.
    Useful for comparing responses with and without constitution.
    """
    return {
        "enabled": USE_CONSTITUTION,
        "loaded": bool(CONSTITUTION_TEXT),
        "constitution_file": os.getenv("CONSTITUTION_FILE", "cambridge_university_v1.txt") if USE_CONSTITUTION else None,
        "constitution_length": len(CONSTITUTION_TEXT) if CONSTITUTION_TEXT else 0
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("AGENT_API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
