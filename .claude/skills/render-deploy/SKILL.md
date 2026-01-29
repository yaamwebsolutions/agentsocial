---
name: render-deploy
description: Render CLI deployment for AgentSocial backend. Use when deploying, monitoring, or managing the FastAPI backend on Render.com. Handles service deployment, log viewing, environment variables, and health checks for the srv-d5qg6onpm1nc738qeg30 backend service.
---

# Render Deployment

This skill manages the AgentSocial backend deployment on Render.com.

## Quick Start

```bash
# Login to Render
render login

# Deploy backend to Render
render deploys create srv-d5qg6onpm1nc738qeg30 --confirm

# Check deployment status
render deploys list srv-d5qg6onpm1nc738qeg30 -o json --confirm

# View service logs
render logs -r srv-d5qg6onpm1nc738qeg30 -o json --limit 100 --confirm
```

## Service Details

| Property | Value |
|----------|-------|
| Service ID | `srv-d5qg6onpm1nc738qeg30` |
| Service URL | https://api.yaam.click |
| Dashboard | https://dashboard.render.com/web/srv-d5qg6onpm1nc738qeg30 |

## Deployment Workflow

### 1. Pre-deploy Checklist

- [ ] Verify main branch has latest changes
- [ ] Run backend tests: `cd backend && pytest tests/ -v`
- [ ] Run linting: `cd backend && ruff check . && ruff format .`
- [ ] Check environment variables are set on Render

### 2. Trigger Deployment

```bash
# Via CLI (recommended)
render deploys create srv-d5qg6onpm1nc738qeg30 -o json --confirm

# Or push to main branch (auto-deploys)
git push origin main
```

### 3. Monitor Deployment

```bash
# Watch deployment status
render deploys list srv-d5qg6onpm1nc738qeg30 -o json --confirm | jq '.[0] | {id, status, commit}'
```

Wait for `status` to be `"live"`.

### 4. Verify Deployment

```bash
# Health check
curl https://api.yaam.click/health

# Check system status
curl https://api.yaam.click/status

# Test Auth0 callback
curl -X POST https://api.yaam.click/auth0/callback -H "Content-Type: application/json" -d '{}'
```

## Common Commands

| Task | Command |
|------|---------|
| List deploys | `render deploys list srv-d5qg6onpm1nc738qeg30 -o json --confirm` |
| View logs | `render logs -r srv-d5qg6onpm1nc738qeg30 -o json --limit 100 --confirm` |
| Cancel deploy | `render deploys cancel <deploy-id> srv-d5qg6onpm1nc738qeg30` |
| Restart service | `render restart srv-d5qg6onpm1nc738qeg30` |
| SSH into service | `render ssh srv-d5qg6onpm1nc738qeg30` |

## Environment Variables

Key variables set on Render:
- `DEEPSEEK_API_KEY` - LLM API access
- `AUTH0_DOMAIN`, `AUTH0_CLIENT_ID`, `AUTH0_CLIENT_SECRET` - Auth0 OAuth
- `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` - GitHub OAuth
- `ADMIN_USER_IDS` - Comma-separated admin email/user IDs
- `USE_REAL_LLM` - Set to `true` for production

## Troubleshooting

### Deployment Stuck in "build_in_progress"

```bash
# Check recent logs
render logs -r srv-d5qg6onpm1nc738qeg30 -o json --limit 200 --confirm | jq -r '.[].message'

# Cancel and retry
render deploys cancel <deploy-id> srv-d5qg6onpm1nc738qeg30
render deploys create srv-d5qg6onpm1nc738qeg30 --confirm
```

### Auth0 400 Bad Request

1. Check Auth0 Application Authentication is set to "Client Secret (Post)"
2. Verify `AUTH0_CLIENT_SECRET` is correctly set on Render
3. Check callback logs: `render logs -r srv-d5qg6onpm1nc738qeg30 -o json --text "auth0" --confirm`

### Service Not Responding

```bash
# Health check
curl https://api.yaam.click/health

# If unhealthy, restart service
render restart srv-d5qg6onpm1nc738qeg30

# Check for crashes in logs
render logs -r srv-d5qg6onpm1nc738qeg30 -o json --level error --confirm
```

## Scripts

See [scripts/](scripts/) for automation helpers:
- `deploy.sh` - Full deployment workflow
- `health-check.sh` - Verify service health
- `logs.sh` - Tail logs with filtering
