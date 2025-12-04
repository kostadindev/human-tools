# Human Tools - LLM Agent with Human Query API

A project with two FastAPI servers:
1. **Agent API**: Gemini LLM agent with LangChain that has access to tools
2. **Human API**: API server that receives queries from the agent

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and add your Google API key:

```bash
cp .env.example .env
```

Edit `.env` and add your Google API key:
```
GOOGLE_API_KEY=your_actual_google_api_key_here
```

Get your Google API key from: https://makersuite.google.com/app/apikey

### 3. Run the Servers

You need to run both servers in separate terminals.

**Terminal 1 - Human API:**
```bash
python human_api.py
```

**Terminal 2 - Agent API:**
```bash
python agent_api.py
```

## Usage

Once both servers are running, you can interact with the agent:

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"input": "Can you ask the human what their favorite color is?"}'
```

The agent will use its `query_human` tool to call the Human API, which will print the query to the console.

## Architecture

```
┌─────────────────┐         ┌─────────────────┐
│   Agent API     │         │   Human API     │
│   (port 8000)   │────────▶│   (port 8001)   │
│                 │  HTTP   │                 │
│ - Gemini LLM    │  POST   │ - Prints query  │
│ - LangChain     │  /query │ - Returns ack   │
│ - Tools         │         │                 │
└─────────────────┘         └─────────────────┘
```

## Project Structure

```
human-tools/
├── agent_api.py       # Agent server with Gemini + LangChain
├── human_api.py       # Human query API server
├── requirements.txt   # Python dependencies
├── .env              # Environment variables (create from .env.example)
├── .env.example      # Example environment variables
└── README.md         # This file
```

## API Endpoints

### Agent API (http://localhost:8000)

- `POST /chat` - Chat with the agent
  - Request: `{"input": "your message"}`
  - Response: `{"output": "agent response"}`

- `GET /health` - Health check

### Human API (http://localhost:8001)

- `POST /query` - Receive query from agent
  - Request: `{"question": "question text", "context": "optional context"}`
  - Response: `{"response": "acknowledgment", "timestamp": "ISO timestamp"}`

- `GET /health` - Health check
