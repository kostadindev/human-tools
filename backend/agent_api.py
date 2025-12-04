"""
Agent API Server
Simple React-style agent that queries a human via API.
"""
import os
import httpx
import threading
from typing import List
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

# Initialize Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

print("🤖 Agent initialized with Gemini 2.5 Flash")


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
            return timeout_msg

        # Get response
        result = pending_callbacks[query_id]["response"]
        pending_callbacks.pop(query_id, None)

        print(f"   ✅ Response received: {result}\n")
        return result

    except Exception as e:
        error_msg = f"Error querying human: {str(e)}"
        print(f"   ❌ Error: {error_msg}\n")
        pending_callbacks.pop(query_id, None) if 'query_id' in locals() else None
        return error_msg


# Tools available to the agent
tools = [query_human]

# Simple React prompt template
template = """Answer the following questions as best you can. You have access to the following tools:

{tools}

IMPORTANT: Only use tools if you truly need them. If you can answer the question directly, do so immediately without using any tools.

Use the following format:

Question: the input question you must answer
Thought: think about whether you can answer this directly or need to use a tool
Action: the action to take, should be one of [{tool_names}] (ONLY if needed)
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

prompt = PromptTemplate.from_template(template)

# Create React agent
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True
)

print("✅ React agent created successfully\n")


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    history: List[Message]


class SuggestionResponse(BaseModel):
    suggestions: List[str]


async def generate_streaming_response(history: List[Message]):
    """Stream agent response to frontend"""
    try:
        # Get the last user message
        last_user_message = ""
        for msg in history:
            if msg.role == "user":
                last_user_message = msg.content

        print(f"\n💬 User: {last_user_message}")

        # Track if we've already shown the waiting message
        shown_waiting_message = False

        # Run agent and stream response
        async for chunk in agent_executor.astream({"input": last_user_message}):
            # Stream tool actions (when agent decides to use a tool)
            if "actions" in chunk and not shown_waiting_message:
                for action in chunk["actions"]:
                    if action.tool == "query_human":
                        yield "\n\n🤔 Asking human for help... please wait for their response.\n\n"
                        shown_waiting_message = True
                        break

            # Stream final output
            elif "output" in chunk:
                yield chunk["output"]

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"❌ {error_msg}")
        yield error_msg


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat with the agent. The agent has access to tools including querying a human.
    Streams the response back to the client.
    """
    return StreamingResponse(
        generate_streaming_response(request.history),
        media_type="text/plain"
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


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "agent-api"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("AGENT_API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
