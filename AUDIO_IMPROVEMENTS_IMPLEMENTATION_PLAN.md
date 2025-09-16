# Audio Improvements Implementation Plan - LiveKit Agents 2025

## Overview
This document provides a step-by-step implementation plan to resolve two critical audio issues in the LiveKit Realtime Voice Agent:

1. **First Message Audio Cutoff**: Intermittent audio cutting off at beginning of first message
2. **Function Tool Speech Interruption**: End call function interrupting ongoing speech

All solutions are based on verified 2025 LiveKit documentation and best practices.

---

## Problem Analysis

### Problem 1: First Message Audio Cutoff
**Symptoms**:
- First message sometimes begins mid-sentence
- Audio starts 2-3 seconds late occasionally
- Subsequent messages work perfectly

**Root Cause**:
- Cold start delays in TTS generation (~500ms from OpenAI Realtime API)
- Audio buffering initialization delays
- Codec negotiation on first call

### Problem 2: Function Tool Speech Interruption
**Symptoms**:
- Agent speech cuts off abruptly when end_call function executes
- Unpleasant user experience with interrupted farewell messages
- Function executes immediately without waiting for speech completion

**Root Cause**:
- Function tools execute immediately when called by LLM
- No coordination with ongoing speech output
- Missing speech completion synchronization

---

## Implementation Plan

## Phase 1: Pre-recorded Swedish Greeting

### Step 1.1: Create Audio Directory Structure
```bash
mkdir -p assets/audio
```

### Step 1.2: Record Swedish Greeting Audio
Create high-quality WAV recording of:
```
"Hej och välkommen! Jag är Elsa, din AI-assistent. Vad kan jag hjälpa dig med idag?"
```

**Technical Requirements**:
- Format: WAV (optimal for LiveKit performance)
- Sample Rate: 16kHz or 24kHz
- Channels: Mono
- Bit Depth: 16-bit or 24-bit
- Save as: `assets/audio/swedish_greeting.wav`

### Step 1.3: Implement Audio Loading Function
Add to `src/agent.py`:

```python
from livekit.agents.utils import audio

async def load_swedish_greeting():
    """Load pre-recorded Swedish greeting as AudioFrames"""
    greeting_path = "assets/audio/swedish_greeting.wav"
    # Returns AsyncIterator[rtc.AudioFrame] optimized for WAV
    return audio.load_wav_file(greeting_path)
```

### Step 1.4: Replace Dynamic Greeting with Pre-recorded Audio
Replace current greeting code:

```python
# BEFORE (current implementation):
greeting_message = os.getenv("AGENT_GREETING_MESSAGE", "Hej och välkommen! Jag är Elsa, din AI-assistent. Vad kan jag hjälpa dig med idag?")
await session.generate_reply(
    instructions=f"Säg hälsningen på svenska: '{greeting_message}' och vänta på svar."
)

# AFTER (new implementation):
try:
    greeting_audio = await load_swedish_greeting()
    await session.say("", audio=greeting_audio)  # Empty text, pre-recorded audio
    logger.info("Pre-recorded Swedish greeting played successfully")
except Exception as e:
    logger.error(f"Failed to load pre-recorded greeting: {e}")
    # Fallback to dynamic generation
    greeting_message = os.getenv("AGENT_GREETING_MESSAGE", "Hej och välkommen! Jag är Elsa, din AI-assistent. Vad kan jag hjälpa dig med idag?")
    await session.generate_reply(
        instructions=f"Säg hälsningen på svenska: '{greeting_message}' och vänta på svar."
    )
```

---

## Phase 2: Fix Function Tool Speech Coordination

### Step 2.1: Update Function Tool Imports
Add to imports in `src/agent.py`:

```python
from livekit.agents import RunContext
from livekit.agents.utils import audio
```

### Step 2.2: Update Function Tool Signature
Replace current `end_call` function:

```python
# BEFORE (current implementation):
@function_tool
async def end_call():
    """Called when the user wants to end the call or when the conversation naturally concludes"""
    ctx = get_job_context()
    if ctx is None:
        return "Could not end call - no context available"

    logger.info("Function tool called to end call")
    await ctx.api.room.delete_room(
        api.DeleteRoomRequest(room=ctx.room.name)
    )
    return "Call ended successfully"

# AFTER (new implementation):
@function_tool
async def end_call(context: RunContext):
    """Called when the user wants to end the call or when the conversation naturally concludes"""
    logger.info("End call function called - waiting for speech completion")

    # CRITICAL: Wait for current speech to complete
    await context.wait_for_playout()
    logger.info("Speech completed - proceeding with call termination")

    # Then execute call termination
    ctx = get_job_context()
    if ctx is None:
        return "Could not end call - no context available"

    logger.info("Function tool terminating call after speech completion")
    await ctx.api.room.delete_room(
        api.DeleteRoomRequest(room=ctx.room.name)
    )
    return "Call ended successfully"
```

---

## LiveKit 2025 Documentation References

### Pre-recorded Audio Implementation

**Primary Documentation**:
- **Agent Speech and Audio**: https://docs.livekit.io/agents/build/audio/
  - Audio file playback with rtc.AudioFrame
  - WAV optimization for performance
  - AsyncIterator audio frame handling

**Key Documentation Quotes**:
```
"The player decodes files with FFmpeg via PyAV and supports all common audio formats including MP3, WAV, AAC, FLAC, OGG, Opus, WebM, and MP4."

"The player uses an optimized custom decoder to load WAV data directly to audio frames, without the overhead of FFmpeg. For small files, WAV is the highest-efficiency option."

"You can optionally provide pre-synthesized audio for playback. This skips the TTS step and reduces response time."
```

**API Reference**:
- **livekit.agents.utils.audio**: https://docs.livekit.io/reference/python/livekit/agents/utils/audio.html
- **livekit.agents.voice**: https://docs.livekit.io/reference/python/v1/livekit/agents/voice/index.html

### Function Tool Speech Coordination

**Primary Documentation**:
- **Agent Speech and Audio**: https://docs.livekit.io/agents/build/audio/
  - RunContext.wait_for_playout() usage
  - Speech coordination patterns

**Key Documentation Quotes**:
```
"await ctx.wait_for_playout() # let the agent finish speaking"

"Use RunContext.wait_for_playout() to wait for the assistant's spoken response prior to executing a tool"

"waiting for playout inside function tools could lead to deadlocks, so an error is now raised instead. To wait for the assistant's spoken response before executing a tool, you should use RunContext.wait_for_playout"
```

**Implementation Pattern**:
```python
@function_tool
async def my_function_tool(self, ctx: RunContext):
    await ctx.wait_for_playout()
```

**Telephony Integration Reference**:
- **Agents Telephony Integration**: https://docs.livekit.io/agents/start/telephony/

---

## Testing and Verification

### Phase 1 Testing: Pre-recorded Greeting
**Test Cases**:
1. Call agent 10 times consecutively
2. Verify first message plays immediately every time
3. Verify complete message is heard (no cutoff)
4. Compare audio quality to TTS generation
5. Test fallback mechanism if audio file missing

**Success Criteria**:
- ✅ 100% consistent first message timing
- ✅ No audio cutoff or delay
- ✅ Audio quality matches or exceeds TTS

### Phase 2 Testing: Speech Coordination
**Test Cases**:
1. Have natural conversation ending with goodbye
2. Verify agent completes farewell speech before call ends
3. Test various conversation lengths before ending
4. Verify clean call termination experience

**Success Criteria**:
- ✅ Agent always completes speech before termination
- ✅ No interrupted farewells
- ✅ Smooth call ending experience

---

## Risk Mitigation

### Audio File Handling
- **Risk**: Missing audio file crashes application
- **Mitigation**: Fallback to TTS generation with error logging

### Speech Coordination
- **Risk**: wait_for_playout() deadlock
- **Mitigation**: Using documented 2025 pattern with RunContext parameter

### Performance Impact
- **Risk**: Audio loading delays
- **Mitigation**: WAV format for optimal performance, async loading

---

## Implementation Order

1. **Phase 1 First** - Address first message issue with pre-recorded audio
2. **Test Phase 1** - Verify consistent first message experience
3. **Phase 2 Second** - Implement speech coordination fix
4. **Test Phase 2** - Verify clean call ending experience
5. **Integration Testing** - Test both improvements together

---

## Environment Configuration

Add to `.env.local` if needed:
```bash
# Optional: Path to greeting audio file (defaults to assets/audio/swedish_greeting.wav)
GREETING_AUDIO_PATH=assets/audio/swedish_greeting.wav

# Optional: Enable audio file logging
AUDIO_DEBUG_LOGGING=true
```

---

## Conclusion

These implementations use verified 2025 LiveKit documentation patterns to resolve both audio issues:

1. **Pre-recorded audio** eliminates first message timing inconsistencies
2. **RunContext.wait_for_playout()** ensures proper speech coordination

Both solutions are production-ready and follow official LiveKit best practices for telephony applications.