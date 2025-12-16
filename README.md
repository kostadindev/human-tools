# Tailor - Multi-Agent Orchestration System

A visual, diagram-driven multi-agent system that enables dynamic orchestration of AI agents and human collaboration. Users can design agent workflows through an interactive diagram interface, and the backend enforces this architecture to control which agents can be accessed.

## Architecture Overview

This application implements a **diagram-driven orchestration pattern** where:
1. Users design agent workflows in a visual diagram (frontend)
2. The diagram structure is sent with every API request
3. The backend parses the diagram and **enforces** it by only allowing the orchestrator to use connected agents/tools
4. The orchestrator coordinates specialized AI agents and human input based on the diagram

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                       Frontend (React)                       │
│  ┌────────────────┐              ┌────────────────────────┐ │
│  │  Chat Interface │◄────────────►│  Diagram Editor        │ │
│  │  (Port 5173)   │              │  (ReactFlow)           │ │
│  └────────────────┘              └────────────────────────┘ │
│           │                                   │              │
│           │                                   │              │
│           └───────────────┬───────────────────┘              │
│                           │ Sends diagram + messages         │
└───────────────────────────┼──────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Agent API (Port 8000)                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Orchestrator Agent                       │  │
│  │         (Only uses tools from diagram)               │  │
│  └──────────┬───────────────┬────────────────┬──────────┘  │
│             │               │                │              │
│    ┌────────▼──────┐ ┌─────▼──────┐ ┌───────▼──────────┐  │
│    │  Analytical   │ │  Creative  │ │   query_human    │  │
│    │  Agent Tool   │ │ Agent Tool │ │   (Tool)         │  │
│    └───────────────┘ └────────────┘ └───────┬──────────┘  │
└─────────────────────────────────────────────┼──────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Human API (Port 8001)                     │
│  - Stores queries from agents                               │
│  - Allows humans to respond asynchronously                  │
│  - Sends callbacks back to Agent API                        │
└─────────────────────────────────────────────────────────────┘
```

## How It Works

### 1. Diagram-Driven Architecture

The visual diagram defines the agent workflow:

**Diagram Structure:**
```typescript
{
  nodes: [
    { id: "orchestrator", type: "orchestrator", label: "🎯 Orchestrator" },
    { id: "agent-1", type: "agent", label: "🤖 Agent 1" },
    { id: "agent-2", type: "agent", label: "🤖 Agent 2" },
    { id: "human", type: "human", label: "👤 Human" }
  ],
  edges: [
    { id: "e1", source: "orchestrator", target: "agent-1" },
    { id: "e2", source: "orchestrator", target: "agent-2" },
    { id: "e3", source: "orchestrator", target: "human" }
  ]
}
```

**This diagram means:**
- Orchestrator can use: `analytical_agent`, `creative_agent`, `query_human`
- If you remove an edge, that tool becomes unavailable

### 2. Diagram Enforcement (Backend)

**Location:** `backend/agent_api.py:194-246`

```python
def get_tools_from_diagram(diagram: Optional[DiagramStructure]) -> List:
    """
    Parse diagram and return only tools that orchestrator is connected to.
    This ENFORCES the diagram architecture.
    """
    # 1. Find orchestrator node
    # 2. Find all edges FROM orchestrator
    # 3. Map connected node types to tools:
    #    - node.type == 'agent' → [analytical_agent, creative_agent]
    #    - node.type == 'human' → [query_human]
    # 4. Return filtered tool list
```

**For each request:**
1. `get_tools_from_diagram(diagram)` extracts allowed tools
2. A new `AgentExecutor` is created with ONLY those tools
3. Orchestrator can only use tools in this filtered list

### 3. Agent Types

#### Orchestrator Agent
- **Role:** Coordinates all other agents and human
- **LLM:** Gemini 2.5 Flash (temp: 0.7)
- **Capabilities:** Decides which specialized agent or human to consult
- **Constraint:** Can only use tools connected in diagram

#### Analytical Agent (Tool)
- **Role:** Logical reasoning, data analysis, structured thinking
- **LLM:** Gemini 2.5 Flash (temp: 0.5 - more focused)
- **Use Cases:** Analysis, comparison, evaluation, problem-solving
- **Wrapped as:** LangChain tool called by orchestrator

#### Creative Agent (Tool)
- **Role:** Brainstorming, ideation, creative problem-solving
- **LLM:** Gemini 2.5 Flash (temp: 0.9 - more creative)
- **Use Cases:** Idea generation, storytelling, innovative solutions
- **Wrapped as:** LangChain tool called by orchestrator

#### Human Agent (Tool)
- **Role:** Human-in-the-loop for judgments, approvals, or domain knowledge
- **Implementation:** API-based asynchronous communication
- **Workflow:**
  1. Agent calls `query_human(question)`
  2. Question sent to Human API (port 8001)
  3. Human responds via UI or API
  4. Callback sent back to Agent API
  5. Agent receives response and continues

## Project Structure

```
human-tools/
├── frontend/                    # React + TypeScript frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── chat.tsx                      # Main chat interface
│   │   │   ├── ArchitectureDiagram.tsx       # Diagram editor (ReactFlow)
│   │   │   ├── MessageList.tsx               # Chat messages display
│   │   │   └── Suggestions.tsx               # Follow-up suggestions
│   │   ├── contexts/
│   │   │   └── DiagramContext.tsx            # Diagram state management
│   │   ├── hooks/
│   │   │   └── useChat.ts                    # Chat logic & API calls
│   │   ├── services/
│   │   │   └── chatService.ts                # API communication
│   │   └── types/
│   │       └── chat.ts                       # TypeScript types
│   └── package.json
│
├── backend/                     # Python backend
│   ├── agent_api.py                          # Main orchestration server
│   │   ├── Orchestrator agent (lines 37-54)
│   │   ├── Analytical agent tool (lines 117-146)
│   │   ├── Creative agent tool (lines 149-178)
│   │   ├── query_human tool (lines 59-114)
│   │   ├── get_tools_from_diagram() (lines 194-246)
│   │   └── API endpoints (lines 310-477)
│   │
│   ├── human_api.py                          # Human interaction server
│   │   ├── Query storage (in-memory)
│   │   ├── POST /query - receive agent questions
│   │   ├── GET /pending-queries - list questions
│   │   ├── POST /respond/{query_id} - human answers
│   │   └── GET /query/{query_id}/response - check for response
│   │
│   └── requirements.txt
│
└── README.md                    # This file
```

## Setup Instructions

### Prerequisites
- Node.js 18+ and npm
- Python 3.9+
- Google API key (for Gemini models)

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file:**
   ```bash
   GOOGLE_API_KEY=your_google_api_key_here
   AGENT_API_PORT=8000
   HUMAN_API_PORT=8001
   AGENT_API_URL=http://localhost:8000
   HUMAN_API_URL=http://localhost:8001
   ```

5. **Start Agent API (Terminal 1):**
   ```bash
   python agent_api.py
   ```

6. **Start Human API (Terminal 2):**
   ```bash
   python human_api.py
   ```

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Create `.env` file (if needed):**
   ```bash
   VITE_API_URL=http://localhost:8000
   ```

4. **Start development server:**
   ```bash
   npm run dev
   ```

5. **Open browser:**
   ```
   http://localhost:5173
   ```

## Usage

### Basic Workflow

1. **Design Your Agent Workflow:**
   - Click "Diagram" tab
   - See the default: Orchestrator → Agent 1, Agent 2, Human
   - Drag nodes to rearrange
   - Drag from node handles to create new connections
   - Remove connections by selecting edge and pressing Delete

2. **Chat with Your System:**
   - Click "Agent" tab
   - Type your question
   - The orchestrator will use only the agents/tools connected in your diagram

3. **Modify Workflow Dynamically:**
   - Switch to "Diagram" tab
   - Remove Human node connection (delete edge)
   - Switch back to "Agent" tab
   - Now orchestrator can't access human - will only use AI agents

### Example Use Cases

#### Research Assistant (All Agents)
```
Diagram: Orchestrator → Analytical Agent, Creative Agent, Human
Query: "Research market trends for electric vehicles"
Flow:
  1. Analytical agent analyzes data and trends
  2. Creative agent brainstorms innovative angles
  3. Human provides domain expertise or validation
  4. Orchestrator synthesizes all inputs
```

#### Pure AI Analysis (No Human)
```
Diagram: Orchestrator → Analytical Agent, Creative Agent
Query: "Compare React vs Vue.js"
Flow:
  1. Analytical agent provides technical comparison
  2. Creative agent suggests use case scenarios
  3. Orchestrator combines insights
```

#### Human-Only Mode
```
Diagram: Orchestrator → Human
Query: "What's your favorite color?"
Flow:
  1. Orchestrator immediately queries human
  2. Human responds via Human API
  3. Orchestrator returns answer
```

## API Reference

### Agent API (Port 8000)

#### POST `/chat`
Chat with orchestrator. Diagram controls available tools.

**Request:**
```json
{
  "history": [
    { "role": "user", "content": "Hello" },
    { "role": "assistant", "content": "Hi there!" }
  ],
  "diagram": {
    "nodes": [...],
    "edges": [...]
  }
}
```

**Response:** Streaming text/plain

**Status Messages:**
- 🔬 Consulting analytical agent...
- 🎨 Consulting creative agent...
- 🤔 Asking human for help...
- ✅ Response received! Processing...

#### POST `/suggest-followups`
Get follow-up question suggestions.

**Request:** Same as `/chat`

**Response:**
```json
{
  "suggestions": ["Can you elaborate?", "Tell me more", ...]
}
```

#### POST `/callback`
Callback endpoint for Human API to send human responses.

**Request:**
```json
{
  "query_id": "uuid",
  "response": "Human answer text"
}
```

#### GET `/health`
Health check endpoint.

### Human API (Port 8001)

#### POST `/query`
Agent submits a query for human.

**Request:**
```json
{
  "question": "What is your opinion on X?",
  "context": "Optional context",
  "callback_url": "http://localhost:8000/callback"
}
```

**Response:**
```json
{
  "query_id": "uuid",
  "message": "Query received"
}
```

#### GET `/pending-queries`
Get all unanswered queries.

**Response:**
```json
[
  {
    "query_id": "uuid",
    "question": "What is X?",
    "context": null,
    "timestamp": "2024-01-01T12:00:00"
  }
]
```

#### POST `/respond/{query_id}`
Human submits response to a query.

**Request:**
```json
{
  "response": "Here is my answer"
}
```

#### GET `/query/{query_id}/response`
Check if human has responded.

**Response:**
```json
{
  "query_id": "uuid",
  "response": "Human answer",
  "is_ready": true
}
```

## Key Technical Details

### Diagram Context (Frontend)

**Location:** `frontend/src/contexts/DiagramContext.tsx`

Manages diagram state globally:
- Updates whenever nodes/edges change
- Serializes to API-friendly format (removes position, adds type)
- Available via `useDiagram()` hook

### Chat Service (Frontend)

**Location:** `frontend/src/services/chatService.ts`

All API calls include diagram:
```typescript
await fetch(`${API_URL}/chat`, {
  method: "POST",
  body: JSON.stringify({ history, diagram })  // diagram included!
});
```

### Orchestrator Prompt Engineering

**Location:** `backend/agent_api.py:252-288`

Critical instructions:
- "ONLY use tools from [{tool_names}]"
- "If user asks to use unavailable tool, state it clearly"
- "Do NOT attempt to use tools not in available tools list"
- "ALWAYS provide a Final Answer"

This ensures the agent:
1. Respects diagram constraints
2. Explains limitations clearly
3. Never crashes trying to use unavailable tools

### Error Handling

**Location:** `backend/agent_api.py:383-427`

Multi-layered approach:
1. **Validation:** Check if tool exists before showing status message
2. **Fallback:** If no response generated, explain available tools
3. **Exception Handling:** Catch parse errors, provide helpful message
4. **User-Friendly:** Always return something meaningful, never raw errors

## Development Notes

### Adding a New Agent

1. **Create the agent tool** in `backend/agent_api.py`:
```python
@tool
def my_new_agent(task: str) -> str:
    """Description of what this agent does."""
    # Implementation
    return result
```

2. **Update `get_tools_from_diagram()`:**
```python
if node.type == 'my_type':
    available_tools.append(my_new_agent)
```

3. **Add to orchestrator prompt:**
```python
template = """...
- my_new_agent: Use for X, Y, Z tasks
..."""
```

4. **Update frontend diagram:** Add new node type to `DiagramContext.tsx`

### Testing Diagram Enforcement

1. Open diagram tab
2. Remove all edges from orchestrator
3. Try asking a question
4. Should see: "No tools connected in diagram, using all tools as fallback"

Or:

1. Remove only Human edge
2. Ask "ask the human what is 5+5"
3. Should see: "I cannot do that because query_human is not available"

### Debugging

**Backend logs show:**
```
🆕 New chat request: abc123
💬 User: Hello
📊 Diagram: 4 nodes, 3 edges
   Orchestrator ACTUALLY connected to: ['🤖 Agent 1', '🤖 Agent 2', '👤 Human']
   Available tools: ['analytical_agent', 'creative_agent', 'query_human']
🔧 Tools enabled from diagram: ['analytical_agent', 'creative_agent', 'query_human']
```

**If agent tries unavailable tool:**
```
⚠️  Agent tried to use unavailable tool: query_human
```

## Future Enhancements

- [ ] Persist diagram configurations
- [ ] User authentication and saved workflows
- [ ] More specialized agents (code, math, research, etc.)
- [ ] Agent execution history and metrics
- [ ] Conditional routing based on query type
- [ ] Multi-step workflows with approval gates
- [ ] Agent collaboration (agents talking to each other)
- [ ] Cost tracking per agent

## License

MIT

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Troubleshooting

**Port already in use:**
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 8001
lsof -ti:8001 | xargs kill -9
```

**CORS errors:**
Check `allow_origins` in both `agent_api.py` and `human_api.py` includes your frontend URL.

**Agent not respecting diagram:**
1. Check browser DevTools → Network → `/chat` request
2. Verify `diagram` field is present in request body
3. Check backend logs for "Available tools: [...]"

**Gemini API errors:**
1. Verify `GOOGLE_API_KEY` in `.env`
2. Check API quota: https://console.cloud.google.com/
3. Ensure billing is enabled on Google Cloud

---

Built with LangChain, React Flow, FastAPI, and Gemini 2.5 Flash.
