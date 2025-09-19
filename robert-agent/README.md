# Robert's Conversational Reception Agent

A sophisticated Swedish conversational agent for professional call reception and intelligent routing.

## 🎯 Features

### **Natural Conversation Flow**
- **One Question at a Time**: Never overwhelms callers with multiple questions
- **Human-like Responses**: Uses natural filler words and confirmations
- **Intelligent Listening**: Adapts questions based on caller responses
- **Graceful Interruptions**: Handles interruptions naturally

### **Intelligent Call Categorization**
- **Insurance Inquiries**: Handles policy questions and comparisons
- **Solar Installation**: Technical support and new installations
- **General Support**: Routes to appropriate specialists
- **Urgency Detection**: Recognizes and prioritizes urgent calls

### **Professional Contact Collection**
- **Natural Integration**: Collects contact info as part of conversation
- **Confirmation Process**: Reads back details for accuracy
- **Flexible Requirements**: Adapts collection based on call type

### **Smart Routing & Escalation**
- **Specialist Handoffs**: Routes to insurance or solar specialists
- **Meeting Proposals**: Suggests consultations when appropriate
- **Human Escalation**: Escalates complex cases smoothly

## 🗣️ Conversation Examples

### Insurance Inquiry
```
Agent: Hej, tack för att du ringde. Jag är företagets assistent. Hur kan jag hjälpa dig idag?
Caller: Jag vill jämföra försäkringar.
Agent: Okej, gäller det din nuvarande försäkring eller är du intresserad av något nytt?
Caller: Min nuvarande, den känns dyr.
Agent: Jag förstår. Vad heter du?
Caller: Anna Svensson.
Agent: Tack Anna. Vill du bli kontaktad på det här numret?
Caller: Ja.
Agent: För att ge dig bästa rådgivning behöver vi göra en genomgång. Vill du att jag föreslår en tid med en rådgivare?
```

### Solar Support
```
Agent: Hej, tack för att du ringde. Jag är företagets assistent. Hur kan jag hjälpa dig idag?
Caller: Min solcellsanläggning fungerar inte.
Agent: Jag förstår att det gäller din solcellsanläggning. Fungerar den inte som den ska?
Caller: Nej, den producerar mycket mindre än förut.
Agent: Kan du se några siffror på displayen eller i appen?
Caller: Ja, det står bara hälften av vad det brukade vara.
Agent: Vad heter du?
Caller: Lars Nordström.
Agent: Det här verkar kräva att någon tittar på anläggningen. Vill du att jag bokar en tekniker?
```

## 🚀 Quick Start

### 1. Setup Environment
```bash
cd robert-agent
cp .env.example .env
# Edit .env with your API keys
```

### 2. Install Dependencies
```bash
pip install -e .
```

### 3. Run in Development
```bash
python agent.py dev
```

### 4. Deploy to Production
```bash
python agent.py start
```

## ⚙️ Configuration

All agent behavior is configured in `robert-agent-config.md`:

### **Core Settings**
- **Language**: Svenska (Swedish)
- **Voice**: Cedar (warm, professional)
- **Workflow**: Hybrid (tasks + agents)
- **Response Length**: Short (~15 words max)

### **Conversation Rules**
- One question at a time
- Natural filler words ("okej", "jag förstår")
- Contact confirmation by reading back
- Graceful error handling

### **Specialist Routing**
- **Insurance**: Policy questions, comparisons
- **Solar**: Technical issues, installations
- **General**: Information requests

## 🏗️ Architecture

### **Workflow Phases**
1. **Greeting & Intake**: Professional reception
2. **Call Categorization**: Understand purpose
3. **Contact Collection**: Natural information gathering
4. **Specialist Routing**: Route to experts
5. **Closing**: Summary and next steps

### **Agent Components**
- **ReceptionistAgent**: Main conversation handler
- **InsuranceSpecialist**: Insurance expertise
- **SolarSpecialist**: Solar system expertise
- **CallCategorizationTask**: Intent understanding

### **Advanced Features**
- **Interruption Handling**: 8-second silence timeout
- **Emotion Detection**: Responds to caller frustration
- **Context Preservation**: Maintains conversation memory
- **Webhook Integration**: Real-time event notifications

## 🛡️ Guardrails

### **What the Agent WON'T Do**
- Give specific prices or legal advice
- Make promises on behalf of specialists
- Repeat the same information multiple times
- Continue with unclear audio without asking once for clarification

### **Error Handling**
- Graceful recovery from technical issues
- Natural acknowledgment of interruptions
- Escalation for out-of-scope requests
- Timeout handling for silent callers

## 📊 Integration

### **Webhook Events**
- Call start/end
- Categorization complete
- Contact information collected
- Specialist handoffs
- Meeting proposals

### **CRM Integration**
- Contact information logging
- Call categorization tracking
- Follow-up scheduling
- Conversation summaries

## 🧪 Testing

The agent handles these test scenarios:
- **Clear Intent**: Direct insurance/solar questions
- **Vague Intent**: "I have a question about my system"
- **Interruption Heavy**: Caller cuts off mid-sentence
- **Silent Caller**: Long pauses, unclear audio
- **Complex Cases**: Multiple issues requiring escalation

## 🎯 Success Metrics

- **Natural Flow**: Conversations feel human-like
- **Accurate Categorization**: Proper specialist routing
- **Complete Contact Collection**: All required info gathered
- **Appropriate Escalation**: Right cases reach specialists
- **Caller Satisfaction**: Professional, helpful experience

---

**Built with LiveKit Agent Template System** - Professional conversational AI for business! 🎯