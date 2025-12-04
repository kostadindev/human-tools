"""
Agent API Server
This server runs a Gemini LLM agent with LangChain that has access to tools.
One of the tools queries the Human API.
"""
import os
import httpx
import json
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

load_dotenv()

app = FastAPI(title="Agent API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)


@tool
def query_human(question: str, context: str = None) -> str:
    """
    Query a human for information or clarification.
    Use this tool when you need human input to answer a question.

    Args:
        question: The question to ask the human
        context: Optional context to provide with the question

    Returns:
        The human's response
    """
    human_api_url = os.getenv("HUMAN_API_URL", "http://localhost:8001")

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{human_api_url}/query",
                json={"question": question, "context": context}
            )
            response.raise_for_status()
            data = response.json()
            return data["response"]
    except httpx.HTTPError as e:
        return f"Error querying human: {str(e)}"


# Create tools list
tools = [query_human]

# Create prompt template with chat history support
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant. You have access to tools including the ability to query a human for information."),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# Create agent
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


class Message(BaseModel):
    role: str  # "user", "assistant", or "system"
    content: str


class ChatRequest(BaseModel):
    history: List[Message]


class SuggestionResponse(BaseModel):
    suggestions: List[str]


def convert_to_langchain_message(message: Message):
    """Convert frontend message format to LangChain message format"""
    if message.role == "user":
        return HumanMessage(content=message.content)
    elif message.role == "assistant":
        return AIMessage(content=message.content)
    elif message.role == "system":
        return SystemMessage(content=message.content)
    return HumanMessage(content=message.content)


async def generate_streaming_response(history: List[Message]):
    """Generate streaming response from the agent"""
    try:
        # Convert message history to LangChain format
        chat_history = []
        last_user_message = ""

        for msg in history:
            if msg.role == "user":
                last_user_message = msg.content
            if msg != history[-1]:  # Don't include the last message in history
                chat_history.append(convert_to_langchain_message(msg))

        # Stream the agent's response
        async for chunk in agent_executor.astream({
            "input": last_user_message,
            "chat_history": chat_history[:-1] if len(chat_history) > 0 else []
        }):
            # Extract the output text from the chunk
            if "output" in chunk:
                text = chunk["output"]
                # Send raw text for frontend to append
                yield text
            elif "actions" in chunk:
                # Agent is using a tool
                for action in chunk["actions"]:
                    yield f"\n[Using tool: {action.tool}]\n"
            elif "steps" in chunk:
                # Tool execution result
                for step in chunk["steps"]:
                    if hasattr(step, 'observation'):
                        yield f"\n[Tool result: {step.observation}]\n"

    except Exception as e:
        yield f"\nError: {str(e)}\n"


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
