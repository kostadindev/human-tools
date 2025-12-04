"""
Human API Server
This server receives queries from the agent and prints them.
"""
import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = FastAPI(title="Human Query API")


class QueryRequest(BaseModel):
    question: str
    context: str | None = None


class QueryResponse(BaseModel):
    response: str
    timestamp: str


@app.post("/query", response_model=QueryResponse)
async def query_human(request: QueryRequest):
    """
    Endpoint that receives queries from the agent.
    For now, it just prints the query and returns a placeholder response.
    """
    timestamp = datetime.now().isoformat()

    print("\n" + "="*50)
    print(f"[{timestamp}] HUMAN QUERY RECEIVED")
    print("="*50)
    print(f"Question: {request.question}")
    if request.context:
        print(f"Context: {request.context}")
    print("="*50 + "\n")

    return QueryResponse(
        response=f"Human received your question: '{request.question}'",
        timestamp=timestamp
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "human-api"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("HUMAN_API_PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
