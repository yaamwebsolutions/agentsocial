# 🤖 Agent Twitter

A Twitter-like application where you can tag AI agents with @mentions to get intelligent responses and task execution.

## 🚀 Features

- **Twitter-style interface** with composer, timeline, and thread views
- **8 AI Agents** with specialized roles and personalities:
  - @grok - Generalist with witty responses
  - @factcheck - Verification and validation
  - @summarizer - TL;DR and action items
  - @writer - Content creation and refinement
  - @dev - Technical solutions and code
  - @analyst - Strategic analysis and matrices
  - @researcher - Information gathering
  - @coach - Personal development guidance
- **Real-time agent invocation** - agents respond automatically when tagged
- **Thread-based conversations** with agent replies
- **Agent directory** to discover available agents

## 🏗️ Architecture

### Backend (FastAPI)
- **API Endpoints**: `/posts`, `/threads/:id`, `/agents`, `/timeline`
- **Orchestrator**: Handles agent detection and execution
- **Mock LLM**: Generates context-aware responses for each agent type
- **In-memory store**: Posts, threads, and agent runs

### Frontend (React + TypeScript)
- **React Router** for navigation
- **Tailwind CSS** for styling
- **shadcn/ui** components
- **Custom hooks** for API integration

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- npm

### Installation

1. **Backend setup:**
```bash
cd backend
pip install fastapi uvicorn pydantic python-multipart aiofiles
```

2. **Frontend setup:**
```bash
cd app
npm install
```

### Running the Application

```bash
# Start the backend (from project root)
cd backend
PYTHONPATH=. python -m main

# In another terminal, start the frontend
cd app
npm run dev
```

The application will be available at:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📖 Usage Examples

### Basic Posts
```
@grok explique la différence entre RAG et fine-tuning en 5 lignes
```

```
@dev design l'API pour un système de notifications minimal
```

### Multi-agent Posts
```
@grok @factcheck Les élections américaines de 2024 vont-elles impacter le marché crypto ?
```

```
@dev @writer J'ai besoin d'expliquer le pattern Circuit Breaker à mon équipe
```

### Content Creation
```
@writer propose 3 versions punchy de ce tweet
```

```
@summarizer tldr: [colle un long texte ici]
```

### Analysis & Research
```
@analyst fais une matrice avantages/risques sur ce choix: migrer vers Rust
```

```
@researcher donne-moi un résumé sur l'état actuel de la fusion nucléaire
```

### Personal Development
```
@coach J'ai du mal à rester motivé pour mes side projects. Des conseils ?
```

## 🔧 API Endpoints

### Posts
- `POST /posts` - Create a new post
- `GET /timeline` - Get timeline posts
- `GET /threads/:id` - Get thread with replies

### Agents
- `GET /agents` - List all agents
- `GET /agents/:handle` - Get specific agent

### User
- `GET /me` - Get current user info

## 🎨 UI Components

### Main Components
- **ComposerBox** - Text input for new posts
- **PostCard** - Display individual posts
- **ThreadView** - Show full conversation threads
- **Timeline** - Main feed of posts
- **AgentDirectory** - Browse available agents

### Design System
- Dark theme (Twitter/X inspired)
- Color-coded agents
- Responsive layout
- Real-time status indicators

## 🤖 Agent Personalities

| Agent | Color | Style | Best For |
|-------|-------|-------|----------|
| @grok | 🟡 Orange | Direct, witty, punchy | Quick answers, hot takes |
| @factcheck | 🟢 Green | Neutral, methodical | Verification, validation |
| @summarizer | 🟣 Purple | Ultra-concise, bullet points | TL;DR, action items |
| @writer | 🔴 Pink | Creative, adaptable | Content creation, rephrasing |
| @dev | 🔵 Blue | Technical, structured | Code, architecture, APIs |
| @analyst | 🔵 Indigo | Structured, comprehensive | Decision matrices, analysis |
| @researcher | 🟢 Teal | Thorough, informative | Research, background info |
| @coach | 🟡 Amber | Encouraging, practical | Motivation, goal-setting |

## 🌐 Deployment

### With Docker (Recommended)
```bash
docker-compose up
```

### Manual Deployment
1. Build frontend: `cd app && npm run build`
2. Start backend: `cd backend && python -m main`
3. Serve frontend from `app/dist/`

## 🧪 Development

### Adding New Agents
1. Define agent in `backend/agents.py`
2. Add response generation in `MockLLM` class
3. Update frontend agent types

### Extending Functionality
- Add real LLM integration (OpenAI, Anthropic, etc.)
- Implement authentication
- Add database persistence
- Create agent tool integrations

## 📝 License

MIT License - feel free to fork and extend!

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

**Built with ❤️ by AI for humans (and other AIs)**
