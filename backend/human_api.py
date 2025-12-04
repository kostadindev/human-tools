"""
Human API Server
Stores queries from agent and allows humans to respond asynchronously.
"""
import os
import uuid
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, List, Optional

load_dotenv()

app = FastAPI(title="Human Query API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
pending_queries: Dict[str, dict] = {}
responses: Dict[str, str] = {}


class QueryRequest(BaseModel):
    question: str
    context: Optional[str] = None
    callback_url: Optional[str] = None


class QueryCreateResponse(BaseModel):
    query_id: str
    message: str


class QueryInfo(BaseModel):
    query_id: str
    question: str
    context: Optional[str]
    timestamp: str


class ResponseSubmit(BaseModel):
    response: str


class ResponseCheck(BaseModel):
    query_id: str
    response: Optional[str]
    is_ready: bool


@app.post("/query", response_model=QueryCreateResponse)
async def create_query(request: QueryRequest):
    """
    Agent submits a query. Store it and return query_id.
    """
    query_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()

    pending_queries[query_id] = {
        "question": request.question,
        "context": request.context,
        "callback_url": request.callback_url,
        "timestamp": timestamp
    }

    print("\n" + "="*60)
    print(f"📥 NEW QUERY RECEIVED [{timestamp}]")
    print("="*60)
    print(f"Query ID: {query_id}")
    print(f"Question: {request.question}")
    if request.context:
        print(f"Context: {request.context}")
    if request.callback_url:
        print(f"Callback URL: {request.callback_url}")
    print("="*60 + "\n")

    return QueryCreateResponse(
        query_id=query_id,
        message="Query received. Waiting for human response."
    )


@app.get("/pending-queries", response_model=List[QueryInfo])
async def get_pending_queries():
    """
    Get all pending queries (that haven't been answered yet).
    """
    pending = []
    for query_id, query_data in pending_queries.items():
        if query_id not in responses:
            pending.append(QueryInfo(
                query_id=query_id,
                question=query_data["question"],
                context=query_data.get("context"),
                timestamp=query_data["timestamp"]
            ))
    return pending


@app.post("/respond/{query_id}")
async def submit_response(query_id: str, response_data: ResponseSubmit):
    """
    Human submits a response to a query.
    """
    if query_id not in pending_queries:
        raise HTTPException(status_code=404, detail="Query not found")

    if query_id in responses:
        raise HTTPException(status_code=400, detail="Query already answered")

    responses[query_id] = response_data.response

    print("\n" + "="*60)
    print(f"✅ RESPONSE SUBMITTED")
    print("="*60)
    print(f"Query ID: {query_id}")
    print(f"Question: {pending_queries[query_id]['question']}")
    print(f"Response: {response_data.response}")

    # Send callback to agent if callback_url was provided
    callback_url = pending_queries[query_id].get("callback_url")
    if callback_url:
        print(f"📤 Sending callback to: {callback_url}")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                callback_response = await client.post(
                    callback_url,
                    json={"query_id": query_id, "response": response_data.response}
                )
                callback_response.raise_for_status()
                print(f"✅ Callback sent successfully")
        except Exception as e:
            print(f"❌ Error sending callback: {e}")

    print("="*60 + "\n")

    return {"message": "Response recorded successfully"}


@app.get("/query/{query_id}/response", response_model=ResponseCheck)
async def check_response(query_id: str):
    """
    Agent polls this endpoint to check if human has responded.
    """
    if query_id not in pending_queries:
        raise HTTPException(status_code=404, detail="Query not found")

    if query_id in responses:
        return ResponseCheck(
            query_id=query_id,
            response=responses[query_id],
            is_ready=True
        )
    else:
        return ResponseCheck(
            query_id=query_id,
            response=None,
            is_ready=False
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "human-api",
        "pending_queries": len([q for q in pending_queries if q not in responses]),
        "answered_queries": len(responses)
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("HUMAN_API_PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
