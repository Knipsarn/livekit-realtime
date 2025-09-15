# Configuration

## Environment Variables

### LiveKit Configuration
- **LIVEKIT_URL**: WebSocket URL for your LiveKit server (e.g., `wss://your-project.livekit.cloud`)
- **LIVEKIT_API_KEY**: API key for LiveKit authentication
- **LIVEKIT_API_SECRET**: API secret for LiveKit authentication

### OpenAI Configuration  
- **OPENAI_API_KEY**: OpenAI API key for Realtime API access

### Runtime Configuration
- **VOICE_NAME**: Voice model for OpenAI Realtime API
  - Options: `marin`, `cedar`, `alloy`, `ember`, `jade`, `steve`
  - Default: `marin`

- **VAD_THRESHOLD**: Voice Activity Detection sensitivity threshold
  - Range: 0.0 to 1.0 (higher = less sensitive)
  - Default: `0.6`

- **VAD_PREFIX_MS**: Milliseconds of audio to include before speech detection
  - Default: `200`

- **VAD_SILENCE_MS**: Milliseconds of silence before stopping speech detection
  - Default: `700`

## VAD Tuning Guidelines

- **Lower threshold** (0.4-0.5): More sensitive, better for quiet speakers but may pick up background noise
- **Higher threshold** (0.7-0.8): Less sensitive, better for noisy environments but may miss quiet speech
- **Shorter silence duration** (400-600ms): More responsive but may cut off pauses
- **Longer silence duration** (800-1000ms): More patient but less responsive

## PSTN Constraints

- Audio quality: 8 kHz G.711 codec on telephone leg
- Recommended speaking style: Clear enunciation, avoid very fast speech
- Optimize VAD settings for telephone-quality audio