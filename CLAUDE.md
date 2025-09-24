# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Deployment and Testing

**CRITICAL: NEVER run local development commands. Only use LiveKit deployment:**
- Deploy agent: `lk agent deploy`
- Test agent: Use the deployed agent URL from LiveKit Cloud
- Configuration: All agent config is in `config/agent.creation.md` (NOT environment variables)

## Project Structure

This is a LiveKit Agent Template System for building sophisticated AI voice agents. The current implementation focuses on Robert's missed call agent with memory capabilities.

### Core Architecture

**Current Active Agent:**
- `src/agent.py` - Main agent with memory system (CallMemory class)
- `config/agent.creation.md` - Active configuration file loaded by agent
- `robert-agent-config.md` - Source configuration (copied to config/)

**Advanced Workflow System (Available but not currently used):**
- `src/workflows/main_workflow.py` - Orchestrates multi-agent workflows
- `src/agents/` - Base agent classes and specialist agents
- `src/tasks/` - Structured data collection tasks

### Workflow Types
- **Single Agent**: Simple conversational agent (currently used)
- **Multi-Agent**: Specialist handoffs (Technical, Billing, Sales)
- **Task-Based**: Structured data collection workflows
- **Hybrid**: Combined task and multi-agent workflows

## Configuration Management

Agent configuration is YAML-based in `config/agent.creation.md`:
```yaml
language: "Svenska"
voice: "marin"
workflow_type: "hybrid"
personality_traits: "calm, professional, conversational, human-like"
prompt: |
  [Detailed Swedish conversational prompt for missed calls]
```

## Key Features of Current Agent

**Memory System:**
- `CallMemory` class tracks caller information persistently
- Function tools: `save_caller_info()`, `get_collected_info()`, `add_call_details()`
- Prevents re-asking for information already provided

**Audio Configuration:**
- Uses OpenAI Realtime model with "marin" voice
- Transcription disabled to prevent audio artifacts
- Swedish language optimized

## Important Development Rules

1. **No Local Dev Execution**: All `if __name__ == "__main__"` blocks removed
2. **Deploy-Only Testing**: Use `lk agent deploy` exclusively
3. **Config-Driven**: Agent behavior controlled via config files, not code
4. **Memory-First**: Always implement memory tools to prevent information loss
5. **Swedish Focus**: Current agent optimized for Swedish missed call handling

## Agent Creation System

The repository includes a template generation system:
- `scripts/create_agent.py` - Generate new agents from templates
- `make create-agent` - Interactive agent creation
- `make demo` - Quick demo agent creation

## Dependencies

Core requirements in `requirements.txt`:
- `livekit-agents[openai]~=1.2` - LiveKit framework with OpenAI integration
- `python-dotenv~=1.0` - Environment variable management
- `pyyaml~=6.0` - YAML configuration parsing
- `aiohttp~=3.9` - HTTP client for webhooks

## Current Branch Context

Working on `robert-demo` branch with deployed agent ID `CA_oq5bG2Q5XRym` for Robert's missed call handling. The agent uses advanced memory capabilities to remember caller information throughout conversations and provides natural Swedish language interaction.