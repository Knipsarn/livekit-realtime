# README for AI Coders - LiveKit Voice Agent Implementation Guide

## Project Overview
This is a production LiveKit voice agent designed for **errand handling** and **missed call management**. The agent acts as a conversational intermediary that collects information, qualifies leads, and determines callback priorities - NOT a sales or support agent.

## Core Agent Type: Errand Handler / Call Intake Specialist
- **Primary Function**: Collect and qualify information for callback
- **Conversation Style**: Natural, human-like dialogue
- **Memory System**: Persistent information tracking during calls
- **Language**: Configurable (Swedish default)

## Technical Architecture

### 1. OpenAI Realtime Integration
```python
# Connection setup in src/agent.py
session = AgentSession(
    llm=openai.realtime.RealtimeModel(
        model="gpt-realtime",  # OpenAI's realtime voice model
        voice="marin",          # Voice selection
        modalities=["audio", "text"],
        temperature=0.9         # Higher = more natural conversation
    )
)
```

**Key Requirements**:
- OpenAI API key with Realtime API access enabled
- Uses WebSocket connection for real-time audio streaming
- No separate STT/TTS - all handled by OpenAI Realtime

### 2. Configuration System (`config/agent.creation.md`)

The agent loads YAML configuration from a markdown file:

```yaml
language: "Svenska"
voice: "marin"  # Options: "cedar", "marin", "shimmer", etc.
workflow_type: "hybrid"
personality_traits: "calm, professional, conversational, human-like"

first_message: >
  Hej, tack för att du ringde. Jag är roberts assistent.
  Hur kan jag hjälpa dig idag?

prompt: |
  [Full system prompt here - see below for structure]
```

### 3. Prompt Engineering Structure

The prompt follows this critical structure:

#### A. Role Definition
```
Du är [Name]'s personliga assistent som svarar på HANS MISSADE SAMTAL.
```
- Always establish WHO the agent represents
- Clarify it's handling MISSED CALLS (not direct support)

#### B. Main Goal Section
```
DITT HUVUDMÅL:
- Samla in tillräckligt med information för att [Name] ska förstå vad personen ringer om
- När du har förstått ärendet, AVSLUTA genom att säga att du ska meddela [Name]
- FÖRSÖK INTE hjälpa eller lösa problem själv - du samlar bara information
```

#### C. Conversation Rules
```
SAMTALSPROCESS:
1. Lyssna på vad personen säger
2. Ställ 1-2 klargörande frågor för att förstå ärendet
3. När du har tillräckligt information, AVSLUTA
4. FÖRSÖK INTE hjälpa mer efter detta
```

#### D. Forbidden Actions
```
FÖRBJUDET:
- Försöka hjälpa eller ge råd
- Ställa fler frågor efter du förstått ärendet
- Robotfraser som "jag förstår"
- GÖR ANTAGANDEN om vad personen vill
```

#### E. Examples (Critical for Training)
```
EXEMPEL på rätt hantering:
Person: "Jag ringde om hemförsäkringar"
Agent: "Vad gäller hemförsäkringarna?"
Person: "Han skulle visa mig alternativ"
Agent: "Bra, då ska jag meddela Robert..."
[AVSLUTA HÄR]
```

### 4. Memory System Implementation

The agent uses a `CallMemory` class with function tools:

```python
class CallMemory:
    def __init__(self):
        self.caller_name = None
        self.caller_phone = None
        self.caller_email = None
        self.call_purpose = None
        self.call_urgency = "normal"
        self.additional_info = []
```

**Function Tools** (decorated with `@function_tool`):
- `save_caller_info()` - Store collected information
- `check_caller_memory()` - Check what's already known
- `save_call_details()` - Add additional context

### 5. Safety Features

```python
# Call limits
self.max_call_duration = 600  # 10 minutes
self.inactivity_timeout = 30  # 30 seconds

# Graceful termination
async def end_call_gracefully(self):
    # Say goodbye in Swedish
    # Wait for audio to complete
    # Delete room to end call
```

### 6. Deployment Configuration

**LiveKit Setup**:
```toml
# livekit.toml
[agent]
entrypoint = "src.agent:entrypoint"
```

**Environment Variables**:
```bash
OPENAI_API_KEY=sk-xxx  # Required
WEBHOOK_URL=https://...  # Optional
```

## Creating New Agents - Step by Step

### 1. Define Agent Purpose
Determine the agent type:
- **Errand Handler**: Collects info for callback
- **Appointment Setter**: Schedules meetings
- **Information Gatherer**: Qualifies leads
- **Message Taker**: Records messages

### 2. Configure Language & Voice
```yaml
language: "English"  # or "Svenska", "Español", etc.
voice: "cedar"       # Match voice to persona
```

### 3. Write System Prompt
Structure your prompt with:
1. **WHO** the agent is
2. **WHAT** their main goal is
3. **HOW** they should converse
4. **WHAT NOT** to do
5. **EXAMPLES** of good/bad interactions

### 4. Set Conversation Parameters
```yaml
advanced:
  model_overrides:
    temperature: 0.9  # 0.7-0.9 for natural conversation
```

### 5. Implement Memory Tools
Always include memory functions to prevent re-asking information:
```python
@function_tool
async def save_caller_info(self, name=None, phone=None):
    # Store information
```

## Prompt Engineering Best Practices

### 1. Be Explicit About Limitations
```
ALDRIG erbjud att "koppla till [Name]" eller "låta [Name] ringa tillbaka"
```

### 2. Use Concrete Examples
Good prompt includes BOTH positive and negative examples:
```
EXEMPEL på rätt hantering: [...]
DÅLIGT EXEMPEL (för många frågor): [...]
```

### 3. Natural Language Rules
```
- LYSSNA först på vad personen säger
- Ha en riktig konversation - ingen robot-script
- Ställ enkla, öppna frågor först: "Vad gäller det?"
```

### 4. Information Collection Strategy
```
1. Get the main issue first
2. Ask 1-2 clarifying questions max
3. Collect name naturally in conversation
4. End when you have enough info
```

## Common Implementation Patterns

### Pattern 1: Missed Call Handler
```yaml
prompt: |
  You handle missed calls for [Business Owner].
  Goal: Collect caller info and reason for calling.
  End with: "I'll make sure [Owner] gets this message."
```

### Pattern 2: Appointment Qualifier
```yaml
prompt: |
  You qualify appointments for [Professional].
  Goal: Determine urgency and type of service needed.
  End with: "I'll have [Professional] call you to schedule."
```

### Pattern 3: Information Collector
```yaml
prompt: |
  You collect initial information for [Service].
  Goal: Gather requirements without providing quotes.
  End with: "Our specialist will contact you with options."
```

## Testing Your Agent

### 1. Deploy to LiveKit
```bash
lk agent deploy
```

### 2. Test Scenarios
- Caller provides info upfront
- Caller is vague initially
- Caller asks for immediate help
- Caller tries to get advice

### 3. Verify Memory System
- Agent remembers name after first mention
- Doesn't re-ask for provided information
- Summarizes correctly at end

## Debugging Tips

### 1. Check Logs
```bash
lk agent logs --agent-id <id> --follow
```

### 2. Common Issues
- **Agent too helpful**: Strengthen "FÖRSÖK INTE hjälpa" rules
- **Asks too many questions**: Add explicit "1-2 questions max" rule
- **Robotic responses**: Increase temperature, add filler words
- **Doesn't end call**: Add clear AVSLUTA examples

### 3. Prompt Iteration
Test and refine by:
1. Recording actual conversations
2. Identifying problem patterns
3. Adding specific examples to prompt
4. Testing edge cases

## Key Technical Terms

- **Errand Handling**: Managing tasks/requests for someone else
- **Call Intake**: Initial information collection
- **Lead Qualification**: Determining callback priority
- **Conversation Flow**: Natural dialogue progression
- **Context Preservation**: Maintaining information across turns
- **Graceful Termination**: Polite call ending

## Integration Points

### Webhook Payload Structure
```json
{
  "call_id": "room_name",
  "conversation": [
    {
      "role": "user/assistant",
      "content": "text",
      "timestamp": 1234567890
    }
  ],
  "duration_seconds": 120,
  "caller_info": {
    "name": "Anna",
    "phone": "+46701234567",
    "purpose": "Insurance quote"
  }
}
```

## Final Checklist for New Agents

- [ ] Clear role definition in prompt
- [ ] Explicit main goal stated
- [ ] Natural conversation rules
- [ ] Memory system implemented
- [ ] Safety timeouts configured
- [ ] Examples provided in prompt
- [ ] Forbidden actions listed
- [ ] Graceful ending implemented
- [ ] Webhook integration (optional)
- [ ] Tested all edge cases