# LiveKit Realtime Voice Agent

A production-ready voice assistant that connects to phone calls via PSTN using LiveKit and OpenAI's GPT-Realtime API with the advanced "marin" voice model.

## Features

- 🎯 **GPT-Realtime Integration**: Uses the latest `gpt-realtime` model (not gpt-4o-realtime-preview)
- 🗣️ **Marin Voice**: High-quality 2025 voice model for natural conversations
- 📞 **PSTN Integration**: Direct phone call support via Telnyx → LiveKit SIP
- ⚡ **Low Latency**: Real-time audio streaming with minimal delay
- 🔄 **Interruption Support**: Natural conversation flow with barge-in capability
- 🎛️ **Configurable VAD**: Tunable Voice Activity Detection settings

## Quick Start

1. **Clone the repository**:
```bash
git clone https://github.com/Knipsarn/livekit-realtime.git
cd livekit-realtime
```

2. **Install dependencies**:
```bash
pip install -e .
```

3. **Configure environment**:
```bash
cp .env.example .env.local
# Edit .env.local with your API keys
```

4. **Run the agent**:
```bash
make dev
```

## Configuration

Copy `.env.example` to `.env.local` and configure:

- **LIVEKIT_URL**: Your LiveKit WebSocket URL
- **LIVEKIT_API_KEY** & **LIVEKIT_API_SECRET**: LiveKit credentials
- **OPENAI_API_KEY**: OpenAI API key with Realtime API access
- **VOICE_NAME**: Voice model (`marin`, `cedar`, etc.)

## Architecture

```
Phone Call → Telnyx → LiveKit SIP → Agent → GPT-Realtime → Marin Voice → Phone
```

## Requirements

- Python 3.9+
- OpenAI API key with Realtime API access
- LiveKit project with SIP configuration
- Telnyx account for PSTN integration

## Development

See `docs/` for detailed configuration and deployment instructions.

## Tech Stack

- **LiveKit Agents 1.2+**: Real-time communication framework
- **OpenAI GPT-Realtime**: Latest 2025 voice model
- **Telnyx**: PSTN connectivity
- **Python 3.9+**: Modern async/await patterns
