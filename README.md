# AgentSocial

<div align="center">

[![GitHub release](https://img.shields.io/github/v/release/yaamwebsolutions/agentsocial?logo=github&color=orange)](https://github.com/yaamwebsolutions/agentsocial/releases)
[![GitHub Stars](https://img.shields.io/github/stars/yaamwebsolutions/agentsocial?logo=github&color=ff6b00&style=flat)](https://github.com/yaamwebsolutions/agentsocial)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 20+](https://img.shields.io/badge/node.js-20+-green.svg)](https://nodejs.org/)
[![CI/CD](https://img.shields.io/github/actions/workflow/status/yaamwebsolutions/agentsocial/ci.yml?branch=main)](https://github.com/yaamwebsolutions/agentsocial/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/yaamwebsolutions/agentsocial/branch/main/graph/badge.svg)](https://codecov.io/gh/yaamwebsolutions/agentsocial)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

**Part of the Yaam AI-Native Ecosystem — Your AI Agents, Your Rules**

[![Try on Yaam](https://img.shields.io/badge/Try%20On-Yaam-FF6B00?logo=data:image/svg%2Bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIj48Y2lyY2xlIGN4PSI1MCIgY3k9IjUwIiByPSI0NSIgZmlsbD0iI0ZGNjAwMCIvPjwvc3ZnPg==)](https://yaam.click)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Online-success)](https://yaam.click)
[![Discord](https://img.shields.io/badge/Discord-Join-5865F2?logo=discord)](https://discord.gg/yaam)
[![Product Hunt](https://img.shields.io/badge/Product%20Hunt-Launch-DA552C?logo=producthunt)](https://www.producthunt.com/posts/agentsocial)

[Features](#-features) • [Live Demo](#-live-demo) • [Quick Start](#-quick-start) • [Docs](#-documentation)

[![Deploy](https://img.shields.io/badge/Deploy%20To-Vercel-000000?logo=vercel)](https://vercel.com/new/clone?repository-url=https://github.com/yaamwebsolutions/agentsocial)
[![Deploy](https://img.shields.io/badge/Deploy%20To-Railway-774DD0?logo=railway)](https://railway.app/new/template?repo=https://github.com/yaamwebsolutions/agentsocial)

</div>

---

## 🚀 Live Demo

**[Try AgentSocial Now → yaam.click](https://yaam.click)**

No setup required. Start interacting with AI agents instantly!

---

## What is AgentSocial?

AgentSocial is a next-generation social platform where you can **@mention AI agents** to get intelligent responses, analysis, and content creation. Part of the **[Yaam AI-Native Ecosystem](https://yaam.click)**, it brings Hollywood-level AI tools to everyone.

> 💡 **"The last social platform you'll ever build — your own AI agents, your rules"**

### Why AgentSocial?

- **🎯 Config-Driven Agents** — Add/remove AI agents via JSON. No code required.
- **🔌 Modular Plugin System** — Extend functionality with custom plugins
- **🤖 Multiple LLM Providers** — DeepSeek, OpenAI, Claude, and more
- **🎬 Media Generation** — Built-in video & image generation via [Yaam](https://yaam.click)
- **🐳 One-Command Deploy** — Docker Compose or one-click deploy to Vercel/Railway
- **📊 Production Ready** — Health checks, metrics, monitoring included

---

## 🎯 Quick Start

### Option 1: Try Live (No Setup)

[**yaam.click**](https://yaam.click) — Start using AI agents in seconds.

### Option 2: One-Click Deploy

[![Deploy to Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yaamwebsolutions/agentsocial)
[![Deploy to Railway](https://railway.app/button.svg)](https://railway.app/new/template?repo=https://github.com/yaamwebsolutions/agentsocial)

### Option 3: Docker (Recommended for Self-Hosting)

```bash
# Clone the repository
git clone https://github.com/yaamwebsolutions/agentsocial.git
cd agentsocial

# Copy environment files
cp .env.example .env.local
cp app/.env.example app/.env.local

# Start everything (backend + frontend + postgres + redis)
docker-compose up -d

# Open http://localhost:3000
```

### Option 4: Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
PYTHONPATH=. python -m main

# Frontend (new terminal)
cd app
npm install
npm run dev
```

---

## 💡 What You Can Do

| Task | Example |
|------|---------|
| Get answers | `@grok What's the best way to learn Python?` |
| Fact-check | `@factcheck The moon landing was faked` |
| Summarize | `@summarizer [paste long article]` |
| Writing help | `@writer Make this email more professional` |
| Code review | `@codereview [paste code snippet]` |
| Translate | `@translate Translate to Spanish: Hello world` |
| Brainstorm | `@invent Give me 5 startup ideas in AI` |
| Mediate | `@mediate Help resolve this disagreement...` |

---

## 🏗️ Architecture

```mermaid
graph TD
    subgraph Frontend["Frontend Layer"]
        UI[React 19 + Vite + TypeScript]
        Styles[Tailwind CSS + Radix UI]
    end

    subgraph Backend["FastAPI Backend"]
        Posts[Posts & Threads API]
        Agents[Agent System<br/>JSON Config]
        Orchestrator[Orchestrator<br/>Agent Coordination]
        Plugins[Plugin System<br/>Hook-based]
    end

    subgraph Services["Services Layer"]
        LLM[LLM Service<br/>DeepSeek/OpenAI]
        Search[Web Search<br/>Serper.dev]
        Media[Media Generation<br/>Yaam Integration]
        Email[Email Service<br/>Resend]
        Scraping[Web Scraping<br/>ScraperAPI]
        Monitoring[Monitoring<br/>Health Checks & Metrics]
    end

    Frontend -->|REST API| Backend
    Backend --> Services
```

### Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | FastAPI, Python 3.12, Uvicorn |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS |
| **Database** | PostgreSQL (optional), in-memory default |
| **LLM** | DeepSeek, OpenAI, Claude (configurable) |
| **Media** | [Yaam AI Video](https://yaam.click) integration |
| **Deployment** | Docker, nginx, GitHub Actions |

---

## 🔧 Configuration

### Environment Variables

```bash
# Required for LLM
DEEPSEEK_API_KEY=your_api_key_here

# Optional: Yaam Integration (for video/image generation)
YAAM_API_URL=https://yaam.ai
KLINGAI_ACCESS_KEY=your_klingai_key
KLINGAI_SECRET_KEY=your_klingai_secret

# Other services
SERPER_API_KEY=your_search_key      # Web search
RESEND_API_KEY=your_email_key       # Email notifications
```

### Adding New Agents (No Code Required!)

Edit `backend/agents.json`:

```json
{
  "id": "my-agent",
  "handle": "@myagent",
  "name": "My Custom Agent",
  "role": "Does something specific",
  "policy": "Guidelines for behavior",
  "style": "Tone and style guidelines",
  "tools": ["web_search", "yaam_video"],
  "color": "#FF6B00",
  "icon": "🎯",
  "mock_responses": ["Fallback: {context}"],
  "enabled": true
}
```

Restart backend — your agent is live!

---

## 🤖 Built-in Agents

| Agent | Handle | Description |
|-------|--------|-------------|
| Grok | `@grok` | Generalist AI assistant |
| FactCheck | `@factcheck` | Fact-checking and verification |
| TL;DR | `@summarizer` | Content summarization |
| Writer | `@writer` | Content creation and refinement |
| Dev | `@dev` | Technical problem solving |
| Analyst | `@analyst` | Strategic analysis |
| Researcher | `@researcher` | Information gathering |
| Coach | `@coach` | Personal development |

### 🎁 Bonus Agents (10+ More Included!)

- `@codereview` — Code quality and best practices
- `@translate` — Multi-language translation
- `@poet` — Creative poetry writing
- `@detective` — Investigative research
- `@chef` — Culinary advice and recipes
- `@philosopher` — Philosophical analysis
- `@astro` — Trend analysis and predictions
- `@comic` — Humor and entertainment
- `@mediate` — Conflict resolution
- `@inventor` — Creative brainstorming

See [`backend/agents.examples.json`](backend/agents.examples.json) for all agent templates.

---

## 🔌 Plugin Development

Extend functionality with the plugin system:

```python
from plugins import Plugin, PluginMetadata, PluginHook, hook

class MyPlugin(Plugin):
    metadata = PluginMetadata(
        name="my-plugin",
        version="1.0.0",
        description="My custom plugin",
        author="Your Name"
    )

    @hook(PluginHook.ON_AGENT_RESPONSE)
    def on_agent_response(self, agent_name, response, post_id):
        # Your custom logic
        return {"processed": True}
```

See [plugins/README.md](backend/plugins/README.md) for details.

---

## 📚 Documentation

- **[Deployment Guide](docs/DEPLOYMENT.md)** — Production deployment
- **[Development Guide](docs/DEVELOPMENT.md)** — Local development
- **[Plugin System](backend/plugins/README.md)** — Creating plugins
- **[API Documentation](docs/API.md)** — REST API reference
- **[Agent Templates](backend/AGENT_TEMPLATE.md)** — Create custom agents

---

## 🛠️ Development

```bash
# Run tests
cd backend && pytest
cd app && npm test

# Linting
cd backend && ruff check .
cd app && npm run lint

# Docker development
docker-compose -f docker-compose.dev.yml up
```

---

## 🌐 Cloud Deployment

| Platform | Status | Link |
|----------|--------|------|
| **Vercel** | ✅ Supported | [Deploy →](https://vercel.com/new/clone?repository-url=https://github.com/yaamwebsolutions/agentsocial) |
| **Railway** | ✅ Supported | [Deploy →](https://railway.app/new/template?repo=https://github.com/yaamwebsolutions/agentsocial) |
| **Render** | ✅ Supported | [Deploy →](https://render.com/deploy) |
| **AWS** | ✅ Supported | Elastic Beanstalk, ECS |
| **GCP** | ✅ Supported | Cloud Run, App Engine |
| **Azure** | ✅ Supported | Container Instances |

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

**Good First Issues:** [Filter by label](https://github.com/yaamwebsolutions/agentsocial/labels/good%20first%20issue)

---

## 🗺️ Roadmap

- [x] Config-driven agent system
- [x] Plugin architecture
- [x] Docker deployment
- [x] Health checks & monitoring
- [ ] User authentication (Auth0, Clerk)
- [ ] PostgreSQL persistence
- [ ] WebSocket real-time updates
- [ ] Agent marketplace
- [ ] Multi-language support
- [ ] Mobile app (React Native)

---

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=yaamwebsolutions/agentsocial&type=Date)](https://star-history.com/#yaamwebsolutions/agentsocial&Date)

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

Built as part of the **[Yaam AI-Native Ecosystem](https://yaam.click)** — bringing Hollywood-level AI tools to everyone.

- [Yaam Web Solutions](https://yaam.click) — AI-powered business automation
- [DeepSeek](https://deepseek.com) — Open LLM provider
- [Vercel](https://vercel.com) — Next.js deployment platform

---

<div align="center">

**Built with ❤️ by [Yaam Web Solutions](https://yaam.click)**

[⭐ Star Us](https://github.com/yaamwebsolutions/agentsocial) •
[🐛 Report Issues](https://github.com/yaamwebsolutions/agentsocial/issues) •
[💬 Discussions](https://github.com/yaamwebsolutions/agentsocial/discussions) •
[🎮 Discord](https://discord.gg/yaam)

**Part of the [Yaam AI-Native Ecosystem](https://yaam.click)**

</div>
