# LiveKit Voice Agent Template

**Create professional, human-sounding voice agents in minutes.**

This template helps you build AI voice agents that can handle phone calls, take messages, schedule appointments, or provide customer service. Perfect for businesses that want 24/7 phone coverage with natural-sounding AI.

## 🎯 What Can These Agents Do?

- **Handle missed calls** - Take messages when you're unavailable
- **Schedule appointments** - Collect booking information
- **Screen calls** - Understand what callers need and route appropriately
- **Customer service** - Answer common questions and escalate complex issues
- **Collect information** - Gather caller details professionally

## 🚀 Quick Start (With AI Assistant)

The easiest way to create an agent is with an AI assistant like Claude Code:

```
Hey Claude, using this template, create a voice agent for:

[Business Owner Name] who is a [type of business]
Language: [Swedish/English/Spanish/etc.]
Purpose: [what the agent should do]
Style: [how it should behave]
```

**Example:**
```
Create an agent for Maria who runs an Italian restaurant called Bella Vista.
Language: English
Purpose: Take reservation requests - get name, phone, date, time, and party size
Style: Friendly and hospitality-focused
```

The AI will automatically fill in all the configuration files for you!

## 📋 Manual Setup

### 1. Prerequisites

- LiveKit Cloud account ([sign up free](https://cloud.livekit.io))
- OpenAI API key with Realtime API access ([get key](https://platform.openai.com/api-keys))
- LiveKit CLI installed:
  ```bash
  curl -sSL https://get.livekit.io/cli | bash
  ```

### 2. Configure Your Agent

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Fill in your `.env` file:
   ```
   LIVEKIT_URL=wss://your-project.livekit.cloud
   LIVEKIT_API_KEY=your_key
   LIVEKIT_API_SECRET=your_secret
   OPENAI_API_KEY=your_openai_key
   ```

3. Edit `config/agent.creation.md` - replace `{{VARIABLES}}` with your details:
   - `{{LANGUAGE}}` - "Svenska", "English", etc.
   - `{{VOICE}}` - "marin", "cedar", "shimmer", etc.
   - `{{FIRST_MESSAGE}}` - Your greeting
   - `{{MAIN_SYSTEM_PROMPT}}` - How the agent should behave

4. Edit `livekit.toml`:
   - Get your subdomain: `lk project list`
   - Replace `{{YOUR_SUBDOMAIN}}` with your LiveKit Cloud subdomain
   - Replace `{{AGENT_NAME}}` with a display name

### 3. Deploy

```bash
# Authenticate with LiveKit Cloud
lk cloud auth

# Deploy your agent
lk agent create
```

### 4. Test

1. Go to [LiveKit Playground](https://cloud.livekit.io/playground)
2. Select your agent
3. Test the conversation!

## 📚 Documentation

- **[AI_AGENT_CREATOR_GUIDE.md](AI_AGENT_CREATOR_GUIDE.md)** - Complete guide for AI assistants to create agents
- **[config/agent.creation.md](config/agent.creation.md)** - Configuration template with examples

## 🎨 Customization Examples

### Change Voice
Edit `config/agent.creation.md`:
```yaml
voice: "shimmer"  # Options: marin, cedar, shimmer, nova, alloy
```

### Make it Sound More Natural
```yaml
advanced:
  model_overrides:
    temperature: 0.9  # Higher = more natural (range: 0.7-1.0)
```

### Change Language
```yaml
language: "English"  # Supported: Svenska, English, Español, Français, Deutsch
```

### Add Webhook for Call Data
1. In `.env`: Add `WEBHOOK_URL=https://your-endpoint.com/calls`
2. In `config/agent.creation.md`: Set `webhook.enabled: true`

## 🏗️ Project Structure

```
.
├── src/
│   └── agent.py              # Main agent code (language-agnostic)
├── config/
│   └── agent.creation.md     # Your agent configuration
├── .env                      # API keys (create from .env.example)
├── livekit.toml             # Deployment config
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container config
├── AI_AGENT_CREATOR_GUIDE.md # Guide for AI assistants
└── README.md                # This file
```

## ✨ Features

- **Multi-language support** - Swedish, English, Spanish, French, German
- **Natural conversation** - Sounds human, not robotic
- **Memory system** - Remembers information during the call
- **Safety features** - Auto hang-up after 10 minutes or 30 seconds of silence
- **Webhook integration** - Get call transcripts and data
- **Telephony ready** - Works with SIP phone systems

## 🔧 Troubleshooting

### Agent sounds robotic
→ Increase `temperature` to 0.9 in `config/agent.creation.md`

### Wrong language/accent
→ Check `language` setting matches your desired language

### Agent asks too many questions
→ Update the system prompt to emphasize "1-2 questions maximum"

### Agent hangs up too early
→ The `end_call` tool triggers when conversation is done. Adjust prompt to clarify when that is.

### Deployment fails
→ Check subdomain in `livekit.toml` matches `lk project list` output

## 📖 Learn More

- [LiveKit Agents Documentation](https://docs.livekit.io/agents/)
- [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime)
- [LiveKit Cloud](https://cloud.livekit.io)

## 🆘 Support

- GitHub Issues: [Report problems](https://github.com/SNM-Integrations/livekit-realtime/issues)
- LiveKit Discord: [community chat](https://livekit.io/discord)

---

**Made with ❤️ using LiveKit Agents and OpenAI Realtime API**
