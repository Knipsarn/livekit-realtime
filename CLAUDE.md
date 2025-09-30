# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **production-ready LiveKit voice agent** designed for errand handling and missed call management. The agent uses OpenAI's Realtime API for natural Swedish conversations with memory persistence.

## Deployment and Testing

**CRITICAL: NEVER run local development commands. Only use LiveKit deployment:**
- Deploy agent: `lk agent deploy`
- Test agent: Use the deployed agent URL from LiveKit Cloud
- Configuration: All agent config is in `config/agent.creation.md`

## Current Project Structure (Cleaned MVP)

```
livekit-realtime/
├── src/
│   └── agent.py              # Main agent with memory system (CallMemory class)
├── config/
│   └── agent.creation.md     # Active configuration file loaded by agent
├── assets/
│   └── greetings/           # Audio greeting files (optional)
├── .env                     # Environment variables (OPENAI_API_KEY)
├── .env.example            # Environment template
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container for deployment
├── livekit.toml          # LiveKit configuration
├── pyproject.toml        # Python project config
├── Makefile             # Build commands
├── README.md           # Technical setup guide
├── README_FOR_AI.md   # AI coder documentation
└── CLAUDE.md         # This file
```

## Core Architecture

### Active Agent Implementation
- `src/agent.py` - Single-file agent with integrated memory system
- `CallMemory` class tracks caller information persistently
- Function tools: `save_caller_info()`, `check_caller_memory()`, `save_call_details()`
- Safety features: 10-minute max duration, 30-second inactivity timeout

### Configuration System
Agent configuration in `config/agent.creation.md`:
```yaml
language: "Svenska"
voice: "marin"
personality_traits: "calm, professional, conversational, human-like"
prompt: |
  [Detailed conversational prompt for missed calls]
```

## Key Features

### Memory System
- Tracks: name, phone, email, purpose, urgency, details
- Prevents re-asking for information already provided
- Accessible via function tools during conversation

### Audio Configuration
- Uses OpenAI Realtime model (`gpt-realtime`)
- Voice options: "marin", "cedar", "shimmer", etc.
- Temperature: 0.9 for natural conversation

### Safety Features
- Maximum call duration: 10 minutes
- Inactivity timeout: 30 seconds
- Graceful termination with Swedish farewell

## CRITICAL: LiveKit Cloud Management

**IMPORTANT: ALL agent management MUST be done via CLI - NOT possible in web dashboard!**
- Creating agents: Use `lk agent deploy`
- Deleting agents: Use `lk agent delete --id <agent_id>`
- Updating agents: Deploy new version via CLI
- **The LiveKit Cloud web dashboard CANNOT create, delete, or update agents**
- **This applies to ALL plans including Ship/Enterprise**

**ABSOLUTELY CRITICAL: The LiveKit CLI is INTERACTIVE and CANNOT be automated!**
- **NEVER attempt to run LiveKit CLI commands automatically**
- **The CLI uses special terminal controls that CANNOT receive automated input**
- **User MUST manually run these commands and respond to prompts**
- **DO NOT try to pipe input, use echo, use subprocess, or any automation**
- **This has been confirmed multiple times - IT IS IMPOSSIBLE TO AUTOMATE**

## Important Development Rules

1. **No Local Dev Execution**: All testing via `lk agent deploy`
2. **Config-Driven Behavior**: Modify `config/agent.creation.md` for changes
3. **Memory-First Design**: Always preserve caller information
4. **Swedish Language Focus**: Default prompts optimized for Swedish

## Agent Type: Errand Handler

This agent is designed for:
- **Missed call handling**: Collecting information when owner unavailable
- **Lead qualification**: Determining callback priority
- **Message taking**: Recording detailed caller information

NOT designed for:
- Sales conversations
- Technical support
- Direct problem solving
- Appointment booking (without human confirmation)

## Common Tasks

### Modify Agent Behavior
1. Edit `config/agent.creation.md`
2. Update the `prompt` section
3. Deploy: `lk agent deploy`

### Add New Memory Fields
1. Edit `CallMemory` class in `src/agent.py`
2. Update `save_caller_info()` function tool
3. Deploy changes

### Change Language/Voice
1. Edit `config/agent.creation.md`
2. Set `language` and `voice` fields
3. Update `prompt` to match language
4. Deploy changes

## Testing Checklist

When testing changes, verify:
- [ ] Agent introduces itself correctly
- [ ] Collects information without being pushy
- [ ] Remembers provided information
- [ ] Ends call after 1-2 clarifying questions
- [ ] Handles silence/inactivity properly
- [ ] Says goodbye before ending call

## Webhook Integration

Optional webhook configuration in `.env`:
```bash
WEBHOOK_URL=https://your-endpoint.com/webhook
```

Payload includes full conversation transcript and extracted caller information.

## Current Deployment

- Branch: `template-system`
- Agent ID: `CA_oq5bG2Q5XRym`
- Purpose: Robert's Swedish missed call handler
- Status: MVP - Production Ready

## Debugging History & Solutions

### Issue 1: "project does not match agent subdomain []" Error
**Symptoms:** `lk agent create` fails with empty subdomain error
**Root Cause:** Missing `subdomain` field in `livekit.toml` or wrong project name
**Solution:**
```toml
[project]
name = "snm"  # Must match LiveKit project name
subdomain = "snm-zzc8jbxg"  # Full subdomain from wss://snm-zzc8jbxg.livekit.cloud
```

### Issue 2: "package livekit-agents version is too old" Error
**Symptoms:** Agent creation fails with version error
**Root Cause:** Outdated package versions in `requirements.txt`
**Solution:**
```txt
livekit-agents>=1.2.0  # Update from >=0.11.0
livekit-plugins-openai>=1.2.0  # Update from >=0.9.0
```

### Issue 3: "open examples\python.pip.Dockerfile: file does not exist"
**Symptoms:** Windows path error when creating agent
**Root Cause:** LiveKit CLI on Windows uses backslash `\` but file system uses forward slash `/`
**Solution:** Copy Dockerfile to root directory as workaround
```bash
cp examples/python.pip.Dockerfile Dockerfile
```

### Issue 4: Agent Picks Up But No Audio
**Symptoms:** Call connects, agent session starts, but caller hears silence
**Root Cause:** Missing Swedish `InputAudioTranscription` configuration
**Solution:** Add to RealtimeModel initialization:
```python
input_audio_transcription=InputAudioTranscription(
    model="whisper-1",
    language="sv",  # Swedish language
    prompt="Svenska konversation med AI-assistent Robert"
)
```

### Issue 5: Multiple Conflicting Agents
**Symptoms:** Broken agent intercepts calls, working agent never gets them
**Root Cause:** Multiple agents deployed to same project
**Solution:** Delete all agents before deploying new one:
```bash
lk agent list
lk agent delete --id <agent_id>  # User must manually confirm
```

## Important Notes

- Always test via LiveKit Cloud Playground
- Configuration changes require redeployment
- Memory system is per-call (not persistent across calls)
- Webhook fires after call completion