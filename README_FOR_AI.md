# AI Coder Guide - LiveKit Voice Agent Template

## Template Overview

This is a **production-ready template** for creating human-like voice agents that excel at errand handling and missed call management. The template focuses on natural conversation, intelligent information gathering, and avoiding over-helping behaviors.

## Core Architecture

### Single-File Agent Design
```python
# src/agent.py - Complete agent implementation
class VoiceAssistant(Agent):
    def __init__(self, config, tools=None):
        self.call_memory = CallMemory()  # Persistent memory system
        # OpenAI Realtime integration
        # Safety monitoring
        # Function tools for memory management
```

### OpenAI Realtime Integration
```python
# Direct WebSocket connection to OpenAI Realtime
session = AgentSession(
    llm=openai.realtime.RealtimeModel(
        model="gpt-realtime",           # OpenAI's voice model
        voice="marin",                  # Voice selection
        modalities=["audio", "text"],   # Both audio and text
        temperature=0.9                 # Natural conversation
    )
)
```

**Critical Requirements**:
- OpenAI API key with Realtime API access
- No separate STT/TTS needed - all handled by OpenAI
- WebSocket-based real-time audio streaming

## Configuration System

### YAML-in-Markdown Format
```yaml
language: "{{LANGUAGE}}"              # Svenska, English, Español
voice: "{{VOICE}}"                    # marin, cedar, shimmer, nova, alloy
personality_traits: "{{PERSONALITY}}" # calm, professional, conversational
temperature: {{TEMPERATURE}}          # 0.7-0.9 for natural conversation

prompt: |
  {{MAIN_SYSTEM_PROMPT}}
```

### Template Variables to Replace
When creating agents, replace these placeholders:
- `{{LANGUAGE}}` - Target language
- `{{VOICE}}` - OpenAI voice selection
- `{{PERSONALITY_TRAITS}}` - Character description
- `{{TEMPERATURE}}` - Conversation naturalness (0.9 recommended)
- `{{FIRST_MESSAGE}}` - Initial greeting
- `{{MAIN_SYSTEM_PROMPT}}` - Complete system prompt

## Prompt Engineering Framework

### 1. Agent Type Classification

**Errand Handler / Message Taker**
- Primary function: Information collection for callback
- Conversation style: Listen, understand, collect, end
- DO NOT: Try to solve problems or provide detailed help
- DO: Collect sufficient information for human follow-up

**Customer Service Agent**
- Primary function: Help if possible, escalate when needed
- Conversation style: Helpful but bounded
- DO: Answer basic questions, schedule callbacks
- DO NOT: Make promises beyond capability

### 2. Prompt Structure Template

```
[ROLE DEFINITION]
Du är [OWNER]'s personliga assistent som svarar på HANS MISSADE SAMTAL.

[MAIN GOAL SECTION]
DITT HUVUDMÅL:
- [Primary objective - be specific]
- [Secondary objective - when to end]
- [What NOT to do - critical boundaries]

[HUMAN CONVERSATION RULES]
VIKTIGAST - VAR MÄNSKLIG:
- LYSSNA först på vad personen säger och svara på DET
- Ha en riktig konversation - ingen robot-script
- [Language-specific natural conversation rules]

[EXPLICIT PROCESS]
SAMTALSPROCESS:
1. [Step 1 - usually listening/greeting]
2. [Step 2 - understanding/clarifying]
3. [Step 3 - information collection]
4. [Step 4 - ending/handoff]

[CONVERSATION RULES]
- [Specific behavioral guidelines]
- [Information gathering strategy]
- [Natural flow requirements]

[FORBIDDEN ACTIONS]
- [Specific phrases to avoid]
- [Behaviors that sound robotic]
- [Over-helping tendencies]

[CONCRETE EXAMPLES]
EXEMPEL på rätt hantering:
[Good conversation example with clear ending]

DÅLIGT EXEMPEL:
[Bad conversation showing what NOT to do]

[FINAL REMINDER]
[Restate the core mission]
```

### 3. Language-Specific Considerations

**Swedish (Svenska)**
- Use "Du/dig" (informal but respectful)
- Avoid "jag förstår" (sounds robotic)
- Natural filler words: "okej", "hm", "ja"
- Professional but warm tone
- Direct question style: "Vad gäller det?"

**English**
- Professional but approachable
- Avoid "I understand your frustration" (overused)
- Natural questions: "What's this about?" "How can I help?"
- Acknowledge without over-empathizing

### 4. Memory System Integration

The agent includes a sophisticated memory system:

```python
class CallMemory:
    def __init__(self):
        self.caller_name = None
        self.caller_phone = None  # Auto-extracted from caller ID
        self.caller_email = None
        self.call_purpose = None
        self.call_urgency = "normal"
        self.additional_info = []

@function_tool
async def save_caller_info(self, name=None, phone=None, email=None, purpose=None):
    """Save information as it's collected during conversation"""

@function_tool
async def check_caller_memory(self):
    """Check what information has already been collected"""
```

**Memory Best Practices**:
- Save information immediately when provided
- Check memory before asking questions
- Use caller ID phone number automatically
- Don't re-ask for information already known

## Agent Creation Patterns

### Pattern 1: Missed Call Handler
```python
# Perfect for: Personal assistants, consultants, small businesses
# Goal: Collect caller info and reason for call
# End with: Promise that owner will call back

prompt_template = """
Du är {owner_name}'s personliga assistent...
DITT HUVUDMÅL:
- Samla information om vad personen ringer angående
- Få namn och telefonnummer för återuppringning
- AVSLUTA när du har tillräcklig information
"""
```

### Pattern 2: Customer Service Screener
```python
# Perfect for: Businesses with support teams
# Goal: Help if possible, collect info for escalation
# End with: Resolution or clear next steps

prompt_template = """
You are a customer service agent for {company_name}...
YOUR MAIN GOAL:
- Help with basic questions when possible
- Collect detailed information for complex issues
- Schedule callbacks or escalate appropriately
"""
```

### Pattern 3: Appointment Qualifier
```python
# Perfect for: Healthcare, professional services
# Goal: Understand needs, check availability
# End with: Scheduled appointment or callback for scheduling

prompt_template = """
You are an appointment coordinator for {business_name}...
YOUR MAIN GOAL:
- Understand the type of appointment needed
- Check basic availability if possible
- Collect contact information for scheduling confirmation
"""
```

## Technical Implementation Details

### Voice and Audio Configuration
```python
# Voice selection impacts personality
voices = {
    "marin": "Professional Swedish female, warm",
    "cedar": "Professional English male, authoritative",
    "shimmer": "Friendly English female, approachable",
    "nova": "Energetic English female, modern",
    "alloy": "Neutral English, versatile"
}

# Temperature affects conversation naturalness
temperature_guide = {
    0.7: "More focused, follows prompt strictly",
    0.8: "Balanced, professional with some flexibility",
    0.9: "Natural, conversational (recommended)",
    1.0: "Very creative, potentially unpredictable"
}
```

### Safety and Monitoring
```python
# Built-in safety features
self.max_call_duration = 600      # 10 minutes max
self.inactivity_timeout = 30      # 30 seconds silence
self.safety_monitor_task = None   # Background monitoring

# Graceful call termination
async def end_call_gracefully(self):
    # Say goodbye in appropriate language
    # Wait for audio completion
    # Delete room to end call
```

### Webhook Integration
```python
# Optional: Send call data after completion
payload = {
    "call_id": tracker.call_id,
    "conversation": tracker.conversation_data,
    "duration_seconds": tracker.get_duration(),
    "caller_info": {
        "name": memory.caller_name,
        "phone": memory.caller_phone,
        "purpose": memory.call_purpose
    }
}
```

## Common Customization Requests

### "Make it more natural"
- Increase temperature to 0.9
- Add more conversational examples
- Include natural filler words in prompt
- Emphasize responding to caller's emotional state

### "Stop asking too many questions"
- Add explicit "1-2 questions maximum" rule
- Include examples of when to STOP asking
- Emphasize information collection vs problem solving
- Show bad examples of over-questioning

### "Handle different languages"
- Replace language in config
- Translate system prompt completely
- Adjust cultural communication norms
- Update voice selection for language

### "Add appointment booking"
- Extend memory system with appointment fields
- Add calendar integration tools
- Include availability checking logic
- Update prompt with scheduling process

### "Make it less robotic"
- Remove formal phrases from forbidden list
- Add emotional recognition and response
- Include varied response templates
- Increase contextual awareness

## Deployment and Testing

### LiveKit Cloud Deployment
```bash
# Deploy to LiveKit Cloud
lk agent deploy

# Monitor in real-time
lk agent logs --agent-id <id> --follow

# Test via LiveKit Playground
# https://cloud.livekit.io/playground
```

### Testing Scenarios
1. **Happy Path**: Clear request, provides info, natural ending
2. **Vague Caller**: Unclear about what they want, needs clarification
3. **Emotional Caller**: Upset or frustrated, needs empathy
4. **Information Provided Upfront**: Caller gives name/info immediately
5. **Silent Periods**: Test inactivity timeout handling
6. **Complex Issues**: Caller needs human assistance

### Quality Metrics
- **Natural Flow**: Does conversation feel human?
- **Information Collection**: Gets necessary details efficiently
- **Appropriate Ending**: Stops at right time with clear next steps
- **Memory Usage**: Doesn't re-ask for provided information
- **Boundary Respect**: Doesn't over-help or make promises

## Troubleshooting Guide

### Agent Sounds Robotic
- Check temperature setting (should be 0.9)
- Review forbidden phrases list
- Add more natural conversation examples
- Remove overly formal language

### Over-Helping Behavior
- Strengthen "information collection only" rules
- Add explicit examples of when to stop
- Include "FÖRSÖK INTE hjälpa" type restrictions
- Show bad examples of over-helping

### Poor Information Collection
- Review memory system integration
- Check function tool implementations
- Ensure caller ID phone extraction works
- Add explicit information gathering steps

### Language/Cultural Issues
- Verify language-appropriate communication style
- Check cultural norms for politeness level
- Adjust formality based on target audience
- Test with native speakers

## Advanced Features

### Multi-Language Support
```yaml
# Template supports multiple languages
language: "Svenska"  # Full Swedish localization
language: "English"  # Professional English
language: "Español"  # Spanish support (requires prompt translation)
```

### Custom Function Tools
```python
# Extend memory system with custom fields
@function_tool
async def save_appointment_preference(self, preferred_time: str, service_type: str):
    """Save appointment-specific information"""

@function_tool
async def check_basic_availability(self, date: str):
    """Check if date has availability (simplified)"""
```

### Webhook Event Types
```python
webhook_events = [
    "call_start",      # Call initiated
    "call_end",        # Call completed
    "information_collected", # Key info gathered
    "escalation_needed",     # Human intervention required
    "appointment_requested"   # Scheduling needed
]
```

## Success Metrics

A well-configured agent should achieve:
- **85%+ natural conversation rating** (human evaluation)
- **90%+ successful information collection** (gets name + purpose)
- **<2 minutes average call duration** (efficient)
- **<10% repeat information requests** (good memory usage)
- **95%+ caller satisfaction** with interaction quality

The key to success is balancing natural conversation with efficient information gathering while respecting the agent's role boundaries.