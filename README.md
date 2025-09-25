# LiveKit Voice Agent - Technical Setup Guide

## Overview
Production-ready LiveKit voice agent with Swedish language support and memory persistence for missed call handling. This agent intelligently collects caller information and determines callback priorities.

## Prerequisites

- LiveKit Cloud Account (free trial available at https://cloud.livekit.io)
- Python 3.11+
- Docker (for deployment)
- OpenAI API key with Realtime API access

## Quick Start

### 1. Clone Repository
```bash
git clone <repository-url>
cd livekit-realtime
```

### 2. Install LiveKit CLI
```bash
# macOS
brew install livekit-cli

# Windows
curl -sSL https://get.livekit.io/cli | bash

# Linux
curl -sSL https://get.livekit.io/cli | sh
```

### 3. Configure LiveKit CLI
```bash
lk cloud auth
# Follow prompts to authenticate with LiveKit Cloud
```

### 4. Set Up Environment Variables
```bash
cp .env.example .env
# Edit .env with your credentials:
# - OPENAI_API_KEY=your_openai_api_key_here
```

### 5. Install Dependencies
```bash
pip install -r requirements.txt
```

## Configuration

### Agent Configuration
Edit `config/agent.creation.md` to customize:
- **language**: Agent language (default: "Svenska")
- **voice**: OpenAI voice selection ("marin", "cedar", etc.)
- **first_message**: Initial greeting
- **prompt**: Full system prompt for agent behavior

### Key Configuration Options
```yaml
language: "Svenska"
voice: "marin"
workflow_type: "hybrid"
personality_traits: "calm, professional, conversational, human-like"

advanced:
  model_overrides:
    primary_model: "gpt-realtime"
    temperature: 0.9
```

## Deployment

### Deploy to LiveKit Cloud
```bash
lk agent deploy
```
This command:
1. Builds and packages your agent
2. Deploys to LiveKit Cloud
3. Returns agent ID (e.g., `CA_oq5bG2Q5XRym`)

### Test Your Agent
After deployment, test via:
1. LiveKit Playground: https://cloud.livekit.io/playground
2. Select your deployed agent
3. Join room and test voice interaction

### Update Deployed Agent
```bash
# Make changes to config/agent.creation.md or src/agent.py
lk agent deploy
# Same agent ID is updated
```

## Core Features

### Memory System
The agent includes a sophisticated memory system (`CallMemory` class) that:
- Remembers caller information during conversation
- Prevents re-asking for already provided information
- Tracks: name, phone, email, purpose, urgency, additional details

### Safety Features
- **Call Duration Limit**: 10 minutes max
- **Inactivity Timeout**: 30 seconds of silence ends call
- **Graceful Termination**: Polite farewell before ending

### Webhook Integration
Optional webhook support for call data persistence:
```bash
# Set in .env
WEBHOOK_URL=https://your-endpoint.com/webhook
```

## Project Structure

```
livekit-realtime/
├── src/
│   └── agent.py              # Main agent implementation
├── config/
│   └── agent.creation.md     # Agent configuration
├── .env                      # Environment variables
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container definition
├── livekit.toml             # LiveKit configuration
└── README_FOR_AI.md         # AI coder documentation
```

## Common Tasks

### View Agent Logs
```bash
lk agent logs --agent-id CA_oq5bG2Q5XRym --follow
```

### List Deployed Agents
```bash
lk agent list
```

### Delete Agent
```bash
lk agent delete --agent-id CA_oq5bG2Q5XRym
```

## Troubleshooting

### Agent Not Responding
1. Check OpenAI API key is valid
2. Verify Realtime API access enabled
3. Review logs: `lk agent logs --agent-id <your-agent-id>`

### Audio Issues
- Ensure `voice` in config matches available OpenAI voices
- Check `temperature` setting (0.7-0.9 recommended)

### Deployment Fails
1. Ensure LiveKit CLI authenticated: `lk cloud auth`
2. Check Docker is running (if local build)
3. Verify all required files present

## Support

- LiveKit Documentation: https://docs.livekit.io
- OpenAI Realtime: https://platform.openai.com/docs/guides/realtime
- Issues: Create issue in repository

## License

MIT License - See LICENSE file for details