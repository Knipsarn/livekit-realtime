# 🎯 LiveKit Voice Agent Template

**Create professional, human-like voice agents that excel at errand handling and missed call management.**

This template produces agents that sound natural, avoid over-helping, and focus on understanding rather than assuming. Perfect for creating assistants that handle missed calls, collect information, and manage errands with human-like conversation skills.

## 🚀 What You Get

### Production-Ready Agent Features
- **Human-like Conversation**: Natural flow, no robotic responses
- **Smart Information Gathering**: Knows when to ask questions and when to stop
- **Memory System**: Remembers what's been said, prevents re-asking
- **Graceful Endings**: Wraps up conversations professionally
- **Safety Features**: Call timeouts and activity monitoring

### OpenAI Realtime Integration
- **Real-time Voice**: Direct audio processing, no delays
- **Swedish & English**: Native language support
- **Voice Options**: "marin", "cedar", "shimmer", "nova", "alloy"
- **Optimized Settings**: Temperature tuned for natural conversation

## 🎯 Perfect For

### Missed Call Handling
"Create an assistant for Robert's insurance business, tasked with handling missed calls and errand handling. The agent should understand what callers want without being pushy, collect just enough information, then politely end the call saying Robert will follow up."

### Professional Services
- **Consultants**: Message taking and appointment qualification
- **Healthcare**: Patient call screening and information collection
- **Real Estate**: Lead qualification and callback scheduling
- **Legal**: Initial client intake and consultation scheduling

### Business Support
- **Customer Service**: Initial triage and information gathering
- **Sales Support**: Lead qualification without being sales-focused
- **Appointment Setting**: Schedule and reschedule with context awareness

## 🎨 Agent Philosophy

### Human-Like Principles
✅ **Listen First**: Respond to what's actually being said
✅ **Natural Flow**: Real conversation, not scripted responses
✅ **One Question at a Time**: Never overwhelm with multiple questions
✅ **Understand Intent**: Ask "what" before assuming "why"
✅ **Know When to Stop**: Collect info and wrap up, don't over-help

### What Makes Agents Sound Human
- **Avoid robot phrases**: Never "I understand" or "I hear what you're saying"
- **React authentically**: Respond to emotional context appropriately
- **Ask open questions first**: "What's this about?" not "Do you want X or Y?"
- **Natural name collection**: Work it into conversation, not first question
- **Graceful exits**: Clear next steps, then end conversation

## 📋 Quick Start

### 1. Setup
```bash
git clone <repository-url>
cd livekit-realtime
cp .env.template .env
# Edit .env with your OPENAI_API_KEY
```

### 2. Configure Your Agent
Edit `config/agent.creation.md` and replace these key variables:

```yaml
language: "Svenska"  # or "English"
voice: "marin"       # or "cedar", "shimmer", "nova", "alloy"
personality_traits: "calm, professional, conversational, human-like"
temperature: 0.9     # Higher = more natural

first_message: >
  Hej, tack för att du ringde. Jag är Roberts assistent.
  Hur kan jag hjälpa dig idag?

# Replace {{MAIN_SYSTEM_PROMPT}} with your prompt
prompt: |
  Du är Roberts personliga assistent som svarar på HANS MISSADE SAMTAL...
```

### 3. Deploy
```bash
# Install LiveKit CLI
curl -sSL https://get.livekit.io/cli | bash
lk cloud auth

# Deploy your agent
lk agent deploy
```

### 4. Test
Visit [LiveKit Playground](https://cloud.livekit.io/playground), select your agent, and test!

## 🎨 Prompt Engineering Guide

### The Secret to Human-Like Agents

The key is in the system prompt structure. Here's what works:

#### 1. **Clear Role Definition**
```
Du är [OWNER]'s personliga assistent som svarar på HANS MISSADE SAMTAL.
```
Always establish WHO the agent represents and WHY they're speaking.

#### 2. **Main Goal Section**
```
DITT HUVUDMÅL:
- Samla information för att [OWNER] ska förstå vad personen ringer om
- När du förstått ärendet, AVSLUTA genom att säga att du ska meddela [OWNER]
- FÖRSÖK INTE hjälpa eller lösa problem själv
```

#### 3. **Human Conversation Rules**
```
VIKTIGAST - VAR MÄNSKLIG:
- LYSSNA först på vad personen säger och svara på DET
- Ha en riktig konversation - ingen robot-script
- !ALDRIG säga "jag förstår" eller "jag hör vad du säger"
```

#### 4. **Explicit Process**
```
SAMTALSPROCESS:
1. Lyssna på vad personen säger
2. Ställ 1-2 klargörande frågor för att förstå ärendet
3. När du har information, AVSLUTA med sammanfattning
4. FÖRSÖK INTE hjälpa mer efter detta
```

#### 5. **Concrete Examples**
Always include both GOOD and BAD examples:
```
EXEMPEL på rätt hantering:
Person: "Jag ringde om hemförsäkringar"
Agent: "Vad gäller hemförsäkringarna?"
Person: "Han skulle visa mig alternativ"
Agent: "Bra, jag meddela Robert att du vill se alternativen. Vad heter du?"
[AVSLUTA HÄR]

DÅLIGT EXEMPEL:
Agent: "Vilken typ av boende har du?" [FÖR MÅNGA FRÅGOR]
Agent: "Hur stor är bostaden?" [FÖRSÖKER HJÄLPA]
```

## 🛠️ Advanced Configuration

### Temperature Settings
```yaml
temperature: 0.7  # More focused, professional
temperature: 0.9  # More natural, conversational (recommended)
```

### Voice Selection Guide
- **"marin"**: Professional Swedish female, warm
- **"cedar"**: Professional English male, authoritative
- **"shimmer"**: Friendly English female, approachable
- **"nova"**: Energetic English female, modern
- **"alloy"**: Neutral English, versatile

### Memory System Usage
The agent automatically tracks:
```python
# Automatically saved during conversation
caller_name = "Anna Svensson"
caller_phone = "+46701234567"
call_purpose = "Insurance options"
```

## 📊 Agent Types & Examples

### Missed Call Handler (Swedish)
```yaml
language: "Svenska"
voice: "marin"
specialization: "call_intake_and_routing"
personality_traits: "calm, professional, conversational, human-like"
# Focus: Collect caller info, understand issue, end with callback promise
```

### Customer Service (English)
```yaml
language: "English"
voice: "cedar"
specialization: "customer_support"
personality_traits: "helpful, patient, professional, solution-focused"
# Focus: Help if possible, escalate complex issues, collect feedback
```

### Appointment Qualifier (English)
```yaml
language: "English"
voice: "shimmer"
specialization: "appointment_screening"
personality_traits: "friendly, efficient, organized, detail-oriented"
# Focus: Understand needs, check availability, schedule or collect info
```

## 🎯 Conversation Quality Tips

### What Makes Agents Sound Natural
1. **React to content**: If someone sounds upset, acknowledge it appropriately
2. **Use context clues**: Phone number from caller ID? Don't ask for it again
3. **Vary responses**: Don't use same phrases every time
4. **Natural timing**: Don't rush to fill silence
5. **Appropriate emotion**: Match caller's energy level

### Common Mistakes to Avoid
❌ **Too many questions**: "What's your name, number, email, and issue?"
❌ **Robot phrases**: "I understand your frustration"
❌ **Assumptions**: "Do you want to change your policy?"
❌ **Over-helping**: Trying to solve instead of collecting info
❌ **Script following**: Ignoring what caller actually said

## 📁 Project Structure

```
livekit-realtime/
├── src/
│   └── agent.py              # Main agent with memory system
├── config/
│   └── agent.creation.md     # Configuration template
├── .env.template            # Environment variables template
├── requirements.txt         # Dependencies
├── Dockerfile              # Container setup
├── livekit.toml           # LiveKit configuration
└── README.md             # This guide
```

## 🔧 Troubleshooting

### Agent Sounds Robotic
- Increase `temperature` to 0.9
- Add more natural conversation examples to prompt
- Remove formal phrases from forbidden list

### Too Many Questions
- Add explicit "1-2 questions max" rule
- Include examples of when to STOP asking
- Emphasize information collection vs helping

### Not Understanding Context
- Improve memory system usage
- Add examples of context-aware responses
- Check caller ID integration

## 📚 Resources

- **[OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime)**: Voice model documentation
- **[LiveKit Agents](https://docs.livekit.io/agents)**: Agent framework guide
- **[Voice Options](https://platform.openai.com/docs/guides/text-to-speech/voice-options)**: Available voices

## 🎉 Success Stories

*"We replaced our old phone system with this agent. Customers love how natural it sounds, and we never miss important calls anymore. It's like having a professional receptionist 24/7."*

*"The agent handles 80% of our appointment scheduling automatically. It's smart enough to know what needs human attention and what it can handle."*

Ready to create your own professional voice agent? Start with the configuration template and deploy in minutes! 🚀