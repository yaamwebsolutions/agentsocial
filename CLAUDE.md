# CLAUDE.md - AI Assistant Guide for AgentSocial

This document provides essential context for AI assistants working with the AgentSocial codebase.

## Project Overview

**AgentSocial** is an AI-powered social platform where users can @mention AI agents to get intelligent responses, analysis, and content creation. Part of the Yaam AI-Native Ecosystem.

**Key Concept**: The agent system is **config-driven** via `backend/agents.json` - no code changes are required to add or modify agents.

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS, Radix UI |
| Backend | FastAPI, Python 3.12+, Uvicorn, Pydantic |
| Database | PostgreSQL (optional), in-memory default |
| LLM | DeepSeek (primary), supports OpenAI/Claude |
| Testing | Pytest (backend), Vitest (frontend) |
| Deployment | Docker, Vercel, Railway |

## Directory Structure

```
agentsocial/
├── app/                          # React/Vite frontend
│   ├── src/
│   │   ├── components/           # React components
│   │   │   └── ui/              # Radix UI component wrappers
│   │   ├── pages/               # Page-level components
│   │   ├── contexts/            # React Context (AuthContext, ThemeContext)
│   │   ├── hooks/               # Custom hooks (useApi.ts)
│   │   ├── lib/                 # Utilities
│   │   ├── types/               # TypeScript type definitions
│   │   └── test/                # Test utilities and tests
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                      # FastAPI backend
│   ├── main.py                  # FastAPI app with all endpoints
│   ├── config.py                # Environment configuration
│   ├── models.py                # Pydantic data models
│   ├── agents.py                # Agent loading and mention extraction
│   ├── store.py                 # In-memory data store
│   ├── orchestrator.py          # Agent execution orchestrator
│   ├── plugins.py               # Plugin system base classes
│   ├── monitoring.py            # Health checks and metrics
│   ├── agents.json              # Agent configuration (editable)
│   ├── services/                # External integrations
│   │   ├── llm_service.py      # DeepSeek/LLM API
│   │   ├── search_service.py   # Serper web search
│   │   ├── scraping_service.py # ScraperAPI
│   │   ├── media_service.py    # KlingAI, Pexels, Pixabay
│   │   ├── email_service.py    # Resend
│   │   ├── auth_service.py     # GitHub OAuth
│   │   └── auth0_service.py    # Auth0 OAuth
│   ├── middleware/              # FastAPI middleware
│   ├── plugins/                 # Plugin implementations
│   ├── tests/                   # Pytest tests
│   └── requirements.txt
│
├── docs/                        # Documentation
│   ├── DEPLOYMENT.md
│   ├── DEVELOPMENT.md
│   └── API.md
│
├── .github/workflows/ci.yml     # CI/CD pipeline
├── docker-compose.yml           # Production Docker
├── docker-compose.dev.yml       # Development Docker
└── vercel.json                  # Vercel deployment
```

## Development Commands

### Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run server (port 8000)
PYTHONPATH=. python -m main

# Linting
ruff check .
ruff format .

# Type checking
mypy *.py services/

# Tests
pytest tests/ -v
pytest tests/ --cov=. --cov-report=html
```

### Frontend

```bash
cd app

# Install dependencies
npm install

# Run dev server (port 5173)
npm run dev

# Build for production
npm run build

# Linting
npm run lint

# Tests
npm test
npm run test:coverage
npm run test:ui
```

### Docker

```bash
# Development with hot-reload
docker-compose -f docker-compose.dev.yml up

# Production
docker-compose up -d
```

## Key API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/posts` | POST | Create post with agent mentions |
| `/timeline` | GET | Get timeline posts |
| `/threads/{id}` | GET | Get thread with replies |
| `/agents` | GET | List all agents |
| `/agents/{handle}` | GET | Get specific agent |
| `/health` | GET | Health check |
| `/status` | GET | Detailed system status |

## Agent System

Agents are defined in `backend/agents.json`. To add a new agent:

```json
{
  "id": "my-agent",
  "handle": "@myagent",
  "name": "My Agent",
  "role": "Description of what this agent does",
  "policy": "Behavior guidelines for the agent",
  "style": "Tone and style for responses",
  "tools": ["web_search"],
  "color": "#FF6B00",
  "icon": "🎯",
  "mock_responses": ["Fallback: {context}"],
  "enabled": true
}
```

**Agent mentions** are extracted via regex pattern `@([a-z0-9_-]+)` in `backend/agents.py`.

## Coding Conventions

### Python (Backend)

- **Async/await** for all I/O operations
- **Pydantic models** for request/response validation
- **Service pattern** for external integrations in `services/`
- **snake_case** for functions/variables
- **PascalCase** for classes
- **Type hints** for all function parameters
- Use `ruff` for linting/formatting

### TypeScript (Frontend)

- **Functional components** with hooks
- **Custom hooks** in `hooks/` for API calls
- **Context API** for state (Auth, Theme)
- **Tailwind CSS** for styling
- **Import alias** `@/` points to `src/`
- **camelCase** for functions/hooks
- **PascalCase** for components and types

### Commit Messages

Use conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `style:` - Formatting
- `refactor:` - Refactoring
- `test:` - Tests
- `chore:` - Maintenance

## Common Patterns

### API Hook Pattern (Frontend)

```typescript
// app/src/hooks/useApi.ts
export function useTimeline(limit: number = 50) {
  const [posts, setPosts] = useState<TimelinePost[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiCall<TimelinePost[]>(`/timeline?limit=${limit}`)
      .then(setPosts)
      .finally(() => setLoading(false));
  }, [limit]);

  return { posts, loading };
}
```

### Endpoint Pattern (Backend)

```python
# backend/main.py
@app.post("/posts", response_model=CreatePostResponse)
async def create_post(request: CreatePostRequest):
    result = await orchestrator.process_post(request.text, request.parent_id)
    return result
```

### Plugin Pattern

```python
# backend/plugins/
from plugins import Plugin, PluginMetadata, PluginHook, hook

class MyPlugin(Plugin):
    metadata = PluginMetadata(
        name="my-plugin",
        version="1.0.0",
        description="Description"
    )

    @hook(PluginHook.ON_POST_CREATE)
    def on_post_create(self, post_id: str, text: str):
        return {"processed": True}
```

## Environment Variables

```bash
# Required
DEEPSEEK_API_KEY=your_key

# Frontend
VITE_API_BASE_URL=http://localhost:8000

# Optional services
SERPER_API_KEY=           # Web search
KLINGAI_ACCESS_KEY=       # Image generation
RESEND_API_KEY=           # Email
GITHUB_CLIENT_ID=         # GitHub OAuth
GITHUB_CLIENT_SECRET=
AUTH0_DOMAIN=             # Auth0 OAuth
AUTH0_CLIENT_ID=

# Feature flags
USE_REAL_LLM=true         # Use LLM or mock responses
```

## Data Flow

1. User posts in frontend: `"Hello @grok!"`
2. `ComposerBox` calls `POST /posts`
3. Backend extracts @mention from text
4. `Orchestrator` creates `AgentRun` and async task
5. `LLMService` generates response
6. Agent reply posted to store
7. Frontend polls `/threads/{id}` to see response

## CI/CD Pipeline

The `.github/workflows/ci.yml` runs:
1. Backend lint (ruff)
2. Backend type check (mypy)
3. Backend tests (pytest with coverage)
4. Frontend lint (eslint)
5. Frontend tests (vitest)
6. Docker build test
7. Security scan (trivy)

## Important Files to Know

| File | Purpose |
|------|---------|
| `backend/main.py` | All REST endpoints |
| `backend/agents.json` | Agent configuration |
| `backend/orchestrator.py` | Agent execution logic |
| `backend/services/llm_service.py` | LLM API integration |
| `app/src/hooks/useApi.ts` | All API call hooks |
| `app/src/components/ComposerBox.tsx` | Post creation with mentions |
| `app/src/contexts/AuthContext.tsx` | Authentication state |

## Testing Guidelines

- Backend: Use pytest fixtures in `conftest.py`
- Frontend: Use testing-library/react with vitest
- Mock LLM responses for tests (`USE_REAL_LLM=false`)
- Test files: `backend/tests/`, `app/src/test/__tests__/`

## Deployment

- **Vercel**: Frontend only via `vercel.json`
- **Railway**: Full stack via `render.yaml`
- **Docker**: `docker-compose.yml` for self-hosting
- Health check endpoint: `GET /health`

## Quick Reference

```bash
# Start everything locally
cd backend && PYTHONPATH=. python -m main &
cd app && npm run dev

# Run all tests
cd backend && pytest
cd app && npm test

# Lint everything
cd backend && ruff check . && ruff format .
cd app && npm run lint

# Add new agent
# Edit backend/agents.json, restart backend
```
