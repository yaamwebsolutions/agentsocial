---
name: gh-ops
description: GitHub CLI operations for AgentSocial repository. Use when creating PRs, managing issues, reviewing code, or automating GitHub workflows. Handles PR creation/merge, branch management, issue tracking, and repository operations for the yaamwebsolutions/agentsocial repo.
---

# GitHub Operations

This skill manages GitHub operations for the AgentSocial repository.

## Quick Start

```bash
# Login to GitHub
gh auth login

# Create pull request
gh pr create --title "Feature name" --body "Description"

# List pull requests
gh pr list

# Merge pull request (with admin bypass if needed)
gh pr merge --admin
```

## Repository Details

| Property | Value |
|----------|-------|
| Owner | yaamwebsolutions |
| Repository | agentsocial |
| Default Branch | main |
| Clone URL | git@github.com:yaamwebsolutions/agentsocial.git |

## Authentication

### Initial Setup

```bash
# Interactive login (opens browser)
gh auth login

# Login with token (headless)
gh auth login --with-token < token.txt

# Check auth status
gh auth status

# Set up git credentials helper
gh auth setup-git
```

### Multiple Accounts

```bash
# Switch accounts
gh auth switch

# View current user
gh auth status
```

## Pull Request Workflow

### Create PR

```bash
# From current branch
gh pr create --title "feat: add feature" --body "Description"

# With template
gh pr create --template .github/pull_request_template.md

# Draft PR
gh pr create --draft

# Assign reviewers
gh pr create --reviewer user1,user2
```

### List PRs

```bash
# All open PRs
gh pr list

# Merged PRs
gh pr list --state merged

# Filter by author
gh pr list --author "@me"

# Search PRs
gh pr list --search "audit"
```

### View PR Details

```bash
# View PR in browser
gh pr view

# View as JSON
gh pr view --json title,state,commits,files

# View PR diff
gh pr diff

# View PR checks
gh pr checks
```

### Merge PR

```bash
# Standard merge
gh pr merge

# Merge with admin bypass (for protected branches)
gh pr merge --admin

# Squash merge
gh pr merge --squash

# Rebase merge
gh pr merge --rebase

# Delete branch after merge
gh pr merge --delete-branch
```

## Branch Operations

```bash
# Create branch
git checkout -b feature/name

# Push to remote
git push -u origin feature/name

# List branches
gh repo view --json defaultBranchRef,refs

# Delete branch
git push -d origin feature/name
```

## Issue Management

```bash
# Create issue
gh issue create --title "Bug title" --body "Description"

# List issues
gh issue list

# View issue
gh issue view 123

# Close issue
gh issue close 123

# Add comment
gh issue comment 123 "Comment text"
```

## Repository Operations

```bash
# View repo info
gh repo view

# View repo stats
gh repo view --json name,description,defaultBranchRef,stargazerCount

# List workflows
gh workflow list

# Trigger workflow
gh workflow run workflow.yml

# List releases
gh release list

# Create release
gh release create v1.0.0 --notes "Release notes"
```

## Git Workflow with gh

```bash
# Standard feature branch workflow
git checkout -b feature/my-feature
# ... make changes ...
git add .
git commit -m "feat: add my feature"
git push -u origin feature/my-feature
gh pr create --title "feat: add my feature" --body "Description"

# After PR review and merge
git checkout main
git pull
gh pr list --state merged
gh pr view <number>
gh pr merge --delete-branch
```

## CI/CD Integration

```bash
# View workflow runs
gh run list

# View specific run
gh run view <run-id>

# View run logs
gh run view <run-id> --log

# Rerun failed workflow
gh run rerun <run-id>

# Watch workflow run
gh run watch <run-id>
```

## Scripts

See [scripts/](scripts/) for automation helpers:
- `pr.sh` - Create PR with template
- `merge.sh` - Merge PR with cleanup
- `cleanup.sh` - Clean up merged branches
