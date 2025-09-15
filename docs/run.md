# Local Development

## Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv && source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -e .
```

3. Copy environment template and fill in your credentials:
```bash
cp .env.example .env.local
```

4. Run in development mode:
```bash
make dev
```

## Expected Log Output

When the agent starts successfully, you should see:
- `connected to LiveKit` - Agent connected to your LiveKit server
- `participant joined: <identity>` - User joined the room
- `greeting sent` - Initial greeting message sent to participant

## Environment Variables

Make sure to set these in your `.env.local`:
- `LIVEKIT_URL` - Your LiveKit WebSocket URL
- `LIVEKIT_API_KEY` - Your LiveKit API key
- `LIVEKIT_API_SECRET` - Your LiveKit API secret
- `OPENAI_API_KEY` - Your OpenAI API key
- `VOICE_NAME` - Voice model (marin, cedar, etc.)