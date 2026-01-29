---
name: vercel-deploy
description: Vercel CLI deployment for AgentSocial frontend. Use when deploying, monitoring, or managing the React/Vite frontend on Vercel. Handles preview deployments, production builds, environment variables, and domain configuration.
---

# Vercel Deployment

This skill manages the AgentSocial frontend deployment on Vercel.

## Quick Start

```bash
# Login to Vercel
vercel login

# Deploy preview
vercel

# Deploy to production
vercel --prod

# List deployments
vercel ls
```

## Project Details

| Property | Value |
|----------|-------|
| Framework | React 19 + Vite |
| Build Command | `npm run build` |
| Output Directory | `app/dist` |
| Install Command | `npm install` |
| Dev Command | `npm run dev` |

## Deployment Workflow

### 1. Pre-deploy Checklist

```bash
cd app

# Install dependencies
npm install

# Run linting
npm run lint

# Run tests
npm test

# Build for production
npm run build
```

### 2. Deploy Preview

```bash
cd app
vercel
```

This creates a preview URL for testing.

### 3. Deploy to Production

```bash
cd app
vercel --prod
```

### 4. Verify Deployment

- Open the production URL
- Check browser console for errors
- Test login flow
- Verify API connectivity to `https://api.yaam.click`

## Common Commands

| Task | Command |
|------|---------|
| Preview deploy | `vercel` |
| Production deploy | `vercel --prod` |
| List deployments | `vercel ls` |
| View deployment info | `vercel inspect <deployment-url>` |
| View logs | `vercel logs` |
| Set environment variable | `vercel env add KEY value` |
| List environment variables | `vercel env ls` |
| Remove domain | `vercel domains rm <domain>` |

## Environment Variables

Required on Vercel:
- `VITE_API_BASE_URL` - Backend API URL (default: `https://api.yaam.click`)

```bash
# Set API base URL
vercel env add VITE_API_BASE_URL production
# Enter: https://api.yaam.click
```

## Project Configuration

The `vercel.json` file configures deployment:

```json
{
  "buildCommand": "cd app && npm install && npm run build",
  "outputDirectory": "app/dist",
  "installCommand": "cd app && npm install",
  "framework": "vite",
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

## Troubleshooting

### Build Failures

```bash
# Check build logs
vercel logs

# Local build test
cd app && npm run build
```

### API Connection Issues

1. Verify `VITE_API_BASE_URL` is set correctly
2. Check backend health: `curl https://api.yaam.click/health`
3. Check CORS settings on backend

### Environment Variables Not Working

Vite requires variables to be prefixed with `VITE_`. If a variable isn't available:

```bash
# Verify it's set
vercel env ls

# Redeploy after changing env vars
vercel --prod
```

## Scripts

See [scripts/](scripts/) for automation helpers:
- `deploy.sh` - Full deployment workflow
- `preview.sh` - Quick preview deployment
- `rollback.sh` - Rollback to previous deployment
