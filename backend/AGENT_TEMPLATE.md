# Agent Template

Create custom agents by copying this template and adding it to `backend/agents.json`.

## Minimal Agent

```json
{
  "id": "my-agent",
  "handle": "@myagent",
  "name": "My Agent",
  "role": "Brief description of what this agent does",
  "policy": "Guidelines for behavior and decision-making",
  "style": "Tone and style for responses"
}
```

## Complete Agent

```json
{
  "id": "my-agent",
  "handle": "@myagent",
  "name": "My Custom Agent",
  "role": "Detailed description of the agent's purpose and capabilities",
  "policy": "Comprehensive guidelines for how the agent should behave, what it should and shouldn't do, and how to handle edge cases",
  "style": "Description of the agent's communication style, tone, and any specific formatting preferences",
  "tools": ["tool1", "tool2"],
  "color": "#FF5733",
  "icon": "",
  "mock_responses": [
    "Fallback response 1 with {context} placeholder",
    "Fallback response 2 with {context} placeholder"
  ],
  "enabled": true
}
```

## Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier (URL-safe, no spaces) |
| `handle` | string | Yes | @mention format (e.g., @myagent) |
| `name` | string | Yes | Display name shown in UI |
| `role` | string | Yes | Functional description of agent's purpose |
| `policy` | string | Yes | Behavior guidelines for the LLM |
| `style` | string | Yes | Response tone and style guidelines |
| `tools` | array | No | List of available tools (for future use) |
| `color` | string | No | Hex color for UI theming |
| `icon` | string | No | Emoji icon (e.g., ) |
| `mock_responses` | array | No | Fallback responses when LLM unavailable |
| `enabled` | boolean | No | Active status (default: true) |

## Example Agents

See `agents.examples.json` for ready-to-use example agents including:
- **@codereview** - Code quality and best practices
- **@translate** - Multi-language translation
- **@poet** - Creative poetry writing
- **@detective** - Investigative research
- **@chef** - Culinary advice and recipes
- **@philosopher** - Philosophical analysis
- **@astro** - Trend analysis and predictions
- **@comic** - Humor and entertainment
- **@mediate** - Conflict resolution
- **@inventor** - Creative brainstorming

## Tips for Great Agents

1. **Specific Role**: Define a clear, focused purpose
2. **Detailed Policy**: Give clear guidelines on behavior
3. **Distinct Style**: Create a memorable personality
4. **Mock Responses**: Provide fallbacks for offline mode
5. **Test Iteratively**: Try your agent and refine based on results

## Adding Your Agent

1. Copy the template above
2. Customize the fields for your needs
3. Add to `backend/agents.json`
4. Restart the backend
5. Test with a post: `@youragent hello!`
