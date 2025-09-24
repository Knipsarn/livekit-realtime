# 🤖 LiveKit Voice Agent Template System

A powerful, fully configurable template system for creating production-ready LiveKit voice agents with modular features and industry-specific configurations.

## ✨ Features

### Core Capabilities
- **🧠 Memory System** - Track and persist conversation information
- **🛡️ Safety Features** - Call duration limits, inactivity detection, disconnect handling
- **📞 Telephony Integration** - Auto-extract phone numbers from SIP, call recording
- **🔗 Webhook Support** - Send conversation data to external systems
- **🌍 Multi-language** - Support for any language with appropriate voice selection
- **🎭 Multiple Personalities** - Formal, casual, consultative, technical styles

### Advanced Features
- **🔄 Multi-Agent Workflows** - Hand off between specialist agents
- **📋 Task Collection** - Structured data gathering with validation
- **📅 Calendar Integration** - Schedule appointments (configurable)
- **💼 CRM Integration** - Sync with customer management systems
- **📧 Email Summaries** - Send conversation summaries automatically

## 🚀 Quick Start

### 1. Interactive Agent Creation

Run the generation wizard to create a new agent interactively:

```bash
python scripts/generate_agent.py
```

The wizard will guide you through:
- Basic agent information (name, language, voice)
- Conversation style and greeting
- Feature selection (memory, safety, webhooks)
- Prompt configuration
- Integration settings

### 2. From Configuration File

Create an agent from a pre-configured YAML file:

```bash
python scripts/generate_agent.py --config templates/examples/personal_assistant.yaml
```

### 3. Quick Demo

Generate a demo agent with minimal configuration:

```bash
python scripts/generate_agent.py --quick
```

## 📁 Project Structure

```
livekit-realtime/
├── config/
│   ├── agent.template.yaml      # Master template with all options
│   └── agent.config.yaml        # Your configured agent
├── src/
│   ├── agent_template.py        # Template agent implementation
│   └── agent.py                 # Your generated agent
├── templates/
│   ├── prompts/                 # Prompt templates by use case
│   │   ├── missed_calls.yaml
│   │   ├── customer_support.yaml
│   │   └── sales.yaml
│   └── examples/                # Example configurations
│       ├── personal_assistant.yaml
│       ├── customer_service.yaml
│       └── technical_support.yaml
├── scripts/
│   └── generate_agent.py        # Agent generation wizard
└── agents/                      # Generated agents directory
    └── [your_agent]/            # Your generated agent
```

## 🔧 Configuration

### Basic Configuration

```yaml
agent:
  name: "Assistant"
  owner: "Your Company"
  language: "English"
  voice: "nova"  # cedar, nova, marin, alloy
  personality_traits: "friendly, professional"
```

### Feature Toggles

Enable only the features you need:

```yaml
# Memory System
memory:
  enabled: true
  auto_extract_phone: true  # Extract from SIP participants
  tracked_fields: ["name", "phone", "email", "purpose"]

# Safety Features
safety:
  enabled: true
  max_call_duration: 600  # 10 minutes
  inactivity_timeout: 30  # 30 seconds

# Integrations
integrations:
  webhook:
    enabled: true
    url: "https://your-webhook.com"
```

### Prompt Templates

Choose from pre-built templates or create custom prompts:

```yaml
prompt:
  template: "conversational"  # conversational, formal, technical, custom
  use_case: "missed_calls"    # missed_calls, support, sales
  industry: "general"          # healthcare, finance, retail, tech

  # Or use custom prompt
  custom_prompt: |
    Your complete custom prompt here...
```

## 🎯 Use Case Examples

### Personal Assistant (Missed Calls)
```bash
# Features: Memory, Safety, Phone extraction
python scripts/generate_agent.py --config templates/examples/personal_assistant.yaml
```

### Customer Support Agent
```bash
# Features: Memory, Webhooks, Multi-agent handoff
python scripts/generate_agent.py --config templates/examples/customer_service.yaml
```

### Technical Support Specialist
```bash
# Features: Task collection, Escalation, Recording
python scripts/generate_agent.py --config templates/examples/technical_support.yaml
```

## 🔌 Integrations

### Webhook Events
- `call_start` - When call begins
- `call_end` - When call ends with full transcript
- `data_collected` - When information is gathered
- `handoff` - When agent hands off to specialist

### Telephony Providers
- LiveKit (default)
- Telnyx
- Twilio

### Calendar Providers
- Google Calendar
- Outlook
- CalDAV

## 🛠️ Advanced Customization

### Adding Custom Features

1. Add feature to template configuration:
```yaml
custom_features:
  my_feature:
    enabled: true
    setting1: "value"
```

2. Implement in agent_template.py:
```python
if config.get("custom_features", {}).get("my_feature", {}).get("enabled"):
    # Your feature implementation
```

### Creating New Prompt Templates

Add new templates to `templates/prompts/`:
```yaml
# templates/prompts/medical.yaml
conversational:
  english: |
    You are a medical office assistant for {{owner}}.
    HIPAA compliance is required...
```

## 📊 Monitoring & Analytics

### Built-in Metrics
- Call duration tracking
- Conversation logging
- Information collection rate
- Safety trigger events

### Webhook Payload Structure
```json
{
  "call_id": "room_name",
  "duration_seconds": 145,
  "conversation": [...],
  "collected_info": {
    "name": "John Doe",
    "phone": "+1234567890"
  },
  "config": {
    "agent_name": "Assistant",
    "language": "English"
  }
}
```

## 🚢 Deployment

### Local Testing
```bash
cd agents/your_agent
pip install -r requirements.txt
cp .env.template .env
# Edit .env with API keys
lk agent dev
```

### Production Deployment
```bash
lk agent deploy
```

## 🔒 Security & Compliance

### Available Compliance Modes
- `none` - Standard operation
- `gdpr` - GDPR compliance features
- `hipaa` - HIPAA compliance for healthcare
- `sox` - SOX compliance for finance

### PII Detection
Enable automatic PII detection and masking:
```yaml
advanced:
  security:
    pii_detection: true
    data_retention_days: 30
```

## 📚 Best Practices

1. **Start Simple** - Enable only features you need
2. **Test Thoroughly** - Use test phone numbers before production
3. **Monitor Safety** - Always enable safety features for production
4. **Secure Webhooks** - Use authentication headers
5. **Version Control** - Track your configurations in git

## 🤝 Contributing

To add new templates or features:
1. Create new template in `templates/`
2. Update generation wizard
3. Test with example configuration
4. Submit pull request

## 📝 License

This template system is part of the LiveKit ecosystem and follows LiveKit's licensing.

---

Built with ❤️ for the LiveKit community