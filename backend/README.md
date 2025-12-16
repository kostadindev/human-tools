# Tailor - LLM Agent with Human Query API

Async callback system where an AI agent can query a human and wait for responses.

**Features:**
- Agent submits queries to Human API with callback URL
- Agent waits asynchronously for callback
- Human API sends callback when human responds
- All storage in-memory (no database needed)
- Timeout after 5 minutes if no response
- React-style LangChain agent with clear tool logging

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

Get your Google API key from: https://makersuite.google.com/app/apikey

### 3. Run the Servers

**Terminal 1 - Human API:**
```bash
python human_api.py
```

**Terminal 2 - Agent API:**
```bash
python agent_api.py
```

**Terminal 3 - Frontend (optional):**
```bash
cd ../frontend
npm run dev
```

## Testing the System

### Option 1: Using the Test Script

When the agent asks a question that requires human input:

**Terminal 3:**
```bash
python test_human_response.py
```

This will:
1. Show all pending queries
2. Let you select one to answer
3. Submit your response
4. Agent receives it within 10 seconds

### Option 2: Manual API Calls

**See pending queries:**
```bash
curl http://localhost:8001/pending-queries
```

**Submit a response:**
```bash
curl -X POST "http://localhost:8001/respond/{query_id}" \
  -H "Content-Type: application/json" \
  -d '{"response": "My favorite color is blue"}'
```

### Option 3: Via Frontend

Open http://localhost:5173 and interact with the agent. When it needs human input, respond through the chat interface.

## How It Works (Callback Architecture)

```
┌─────────────────┐                    ┌─────────────────┐
│   Agent API     │                    │   Human API     │
│   (port 8000)   │                    │   (port 8001)   │
│                 │                    │                 │
│  1. Agent calls │  POST /query       │  Stores query   │
│     query_human │  + callback_url    │  + callback URL │
│                 ├───────────────────▶│  Returns ID     │
│                 │                    │                 │
│  2. Agent waits │                    │                 │
│     threading.  │                    │                 │
│     Event()     │                    │                 │
│       ⏸️         │                    │                 │
│                 │                    │  POST /respond  │
│                 │                    │  /{id}          │
│                 │                    │◀────────────────┤ Human
│                 │                    │                 │
│                 │  POST /callback    │  3. Sends       │
│  4. Wakes up!   │  {query_id,        │     callback    │
│     Event.set() │   response}        │                 │
│       ▶️         │◀───────────────────┤                 │
│                 │                    │                 │
│  5. Returns     │                    │                 │
│     response    │                    │                 │
└─────────────────┘                    └─────────────────┘
```

## Project Structure

```
backend/
├── agent_api.py              # Agent server with Gemini + LangChain
├── human_api.py              # Human query API server
├── test_human_response.py    # Interactive script to respond to queries
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables
├── .env.example             # Example environment variables
└── README.md                # This file

frontend/
└── (React app for UI)
```

## API Endpoints

### Agent API (http://localhost:8000)

- `POST /chat` - Chat with the agent
  - Request: `{"history": [{"role": "user", "content": "message"}]}`
  - Response: Streaming text

- `POST /callback` - Receive callback from Human API (internal)
  - Request: `{"query_id": "...", "response": "..."}`
  - Response: `{"message": "Callback received"}`

- `POST /suggest-followups` - Get follow-up suggestions
- `GET /ping` - Wake up server
- `GET /health` - Health check

### Human API (http://localhost:8001)

- `POST /query` - Agent submits a query
  - Request: `{"question": "...", "context": "...", "callback_url": "..."}`
  - Response: `{"query_id": "uuid", "message": "..."}`

- `GET /pending-queries` - Get all unanswered queries
  - Response: `[{"query_id": "...", "question": "...", "timestamp": "..."}]`

- `POST /respond/{query_id}` - Human submits response
  - Request: `{"response": "answer text"}`
  - Response: `{"message": "Response recorded"}`

- `GET /query/{query_id}/response` - Agent polls for response
  - Response: `{"query_id": "...", "response": "...", "is_ready": true/false}`

- `GET /health` - Health check with stats

## Example Flow

**Terminal 1 (Human API):**
```
python human_api.py
# Output: Server running on port 8001
```

**Terminal 2 (Agent API):**
```
python agent_api.py
# Output:
# 🤖 Agent initialized with Gemini 2.5 Flash
# ✅ React agent created successfully
```

**Terminal 3 (Frontend or curl):**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"history": [{"role": "user", "content": "What is my favorite color?"}]}'
```

**Back in Terminal 2 (Agent logs):**
```
💬 User: What is my favorite color?

🔧 TOOL CALLED: query_human
   Question: What is your favorite color?
   Query ID: abc-123-def
   ⏳ Waiting for human response (via callback)...

[Agent is waiting asynchronously...]
```

**Terminal 1 (Human API logs when you respond):**
```
✅ RESPONSE SUBMITTED
Query ID: abc-123-def
Question: What is your favorite color?
Response: Blue
📤 Sending callback to: http://localhost:8000/callback
✅ Callback sent successfully
```

**Terminal 4 (Respond to query):**
```bash
python test_human_response.py
# Select query and type: "Blue"
```

**Back in Terminal 2 (Agent receives callback):**
```
📞 CALLBACK RECEIVED
   Query ID: abc-123-def
   Response: Blue

   ✅ Response received: Blue

Final Answer: Your favorite color is Blue.
```
