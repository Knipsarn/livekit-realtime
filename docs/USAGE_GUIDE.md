# 📖 LiveKit Agent Template - Usage Guide

## 🎯 Overview

This template system allows you to create sophisticated AI voice agents with minimal configuration. Simply fill out the `agent.creation.md` template and run the generation script to get a complete, production-ready agent.

## 🚀 Getting Started

### Step 1: Choose Your Workflow Type

The template supports four main patterns:

#### **🔹 Single Agent** (`single_agent`)
- **Best for**: Simple conversations, basic Q&A, minimal complexity
- **Features**: One agent handles everything
- **Use cases**: FAQ bots, simple information gathering

#### **🔹 Multi-Agent** (`multi_agent`)
- **Best for**: Customer service, complex inquiries requiring specialists
- **Features**: Agent handoffs, specialist routing, escalation paths
- **Use cases**: Technical support, billing inquiries, sales

#### **🔹 Task-Based** (`task_based`)
- **Best for**: Structured data collection, compliance requirements
- **Features**: Step-by-step workflows, data validation, consent collection
- **Use cases**: Medical intake, survey collection, onboarding

#### **🔹 Hybrid** (`hybrid`)
- **Best for**: Enterprise applications requiring both structure and flexibility
- **Features**: Combines tasks and multi-agent workflows
- **Use cases**: Healthcare triage, complex service workflows

### Step 2: Configure Your Agent

#### **Essential Configuration**
```yaml
# Core Identity
agent_name: "CustomerService"     # Your agent's name
owner_name: "Acme Corporation"    # Your company/personal name
language: "English"              # Primary language
voice: "cedar"                   # OpenAI voice selection

# Business Context
business_type: "retail"          # personal, consulting, retail, healthcare
use_case: "customer_support"     # missed_calls, support, sales, scheduling
workflow_type: "multi_agent"     # single_agent, multi_agent, task_based, hybrid
```

#### **Agent Personality**
```yaml
personality_traits: "friendly, professional, efficient"
conversation_style: "consultative"     # formal, casual, consultative
response_length: "medium"              # short, medium, detailed
```

#### **First Message**
```yaml
first_message: >
  Hello! You've reached Acme Corporation. I'm CustomerService,
  and I'm here to help. Who am I speaking with?
```

### Step 3: Enable Features

#### **Multi-Agent Workflows**
```yaml
workflow:
  handoff_triggers: "intent_based"      # keyword_based, intent_based, tool_based
  context_preservation: true           # Maintain conversation history
  max_handoffs: 5                      # Prevent infinite loops

agents:
  secondary:
    enabled: true
    name: "TechnicalSupport"
    specialization: "technical_issues"

  escalation:
    enabled: true
    name: "Manager"
    specialization: "complex_issues"
```

#### **Structured Tasks**
```yaml
tasks:
  consent_collection:
    enabled: true
    required: false                     # Block call if consent denied

  information_gathering:
    enabled: true
    required_fields: "name,phone,email"
    validation_strict: true
```

#### **Integrations**
```yaml
integrations:
  webhook:
    enabled: true
    url: "https://your-api.com/events"
    events: "call_start,call_end,booking"

  calendar:
    enabled: true
    provider: "google"                  # google, outlook, caldav
    timezone: "America/New_York"
```

## 🛠️ Generation Process

### Interactive Mode (Recommended)
```bash
python scripts/create_agent.py --output-dir my-agent
```

The wizard will ask you questions like:
- What is the agent's name?
- What language should it use?
- Enable multi-agent workflows?
- Enable webhook integration?

### Non-Interactive Mode
```bash
# Edit config/agent.creation.md first
python scripts/create_agent.py \
  --output-dir my-agent \
  --non-interactive
```

### Custom Configuration
```bash
# Use your own config file
python scripts/create_agent.py \
  --config my-custom-config.md \
  --output-dir my-agent
```

## 📁 Generated Structure

After generation, you'll get:

```
my-agent/
├── agent.py                 # Main entry point
├── config/
│   └── CustomerService.md   # Your final configuration
├── src/
│   ├── agents/              # Agent implementations
│   ├── tasks/               # Task workflows
│   └── workflows/           # Orchestration logic
├── .env.example            # Environment template
├── pyproject.toml          # Dependencies
├── README.md               # Agent-specific documentation
└── Makefile               # Common commands
```

## 🚀 Running Your Agent

### Development Mode
```bash
cd my-agent
cp .env.example .env
# Edit .env with your API keys
pip install -e .
python agent.py dev
```

### Production Mode
```bash
python agent.py start
```

## 🎛️ Configuration Examples

### Example 1: Samuel's Missed Call Assistant
```yaml
title: "Samuel's Personal Assistant"
agent_name: "Jim"
owner_name: "Samuel"
language: "Svenska"
voice: "cedar"
workflow_type: "task_based"
business_type: "personal"
use_case: "missed_calls"

first_message: >
  Hej, du har nått Samuel. Jag är Jim, hans assistent.
  Han kan inte svara just nu, men jag hjälper gärna till
  att ta ett meddelande. Vem pratar jag med?

tasks:
  information_gathering:
    enabled: true
    required_fields: "name,phone"

tools:
  - name: "calendar_booking"
    enabled: true
    type: "booking"
    description: "Boka en tid för Samuel att ringa upp"

  - name: "log_note"
    enabled: true
    type: "logging"
    description: "Spara meddelande för Samuel"
```

### Example 2: Healthcare Triage Agent
```yaml
title: "Medical Office Triage Assistant"
agent_name: "HealthAssistant"
business_type: "healthcare"
workflow_type: "hybrid"
language: "English"

tasks:
  consent_collection:
    enabled: true
    required: true

  information_gathering:
    enabled: true
    required_fields: "name,symptoms,urgency,insurance"

agents:
  secondary:
    enabled: true
    name: "NurseAgent"
    specialization: "medical_assessment"

  escalation:
    enabled: true
    name: "DoctorAgent"
    specialization: "complex_medical"

security:
  compliance_mode: "hipaa"
  pii_detection: true
```

### Example 3: E-commerce Support Agent
```yaml
title: "Online Store Support"
agent_name: "ShopAssistant"
business_type: "retail"
workflow_type: "multi_agent"

agents:
  secondary:
    enabled: true
    name: "OrderSupport"
    specialization: "order_inquiries"

  escalation:
    enabled: true
    name: "ReturnSpecialist"
    specialization: "returns_refunds"

tools:
  - name: "order_lookup"
    enabled: true
    type: "search"
    description: "Look up customer orders"

  - name: "process_return"
    enabled: true
    type: "custom"
    description: "Initiate return process"

integrations:
  crm:
    enabled: true
    provider: "shopify"
    auto_create_contacts: true
```

## 🔧 Customization

### Adding Custom Tools
1. Edit your agent configuration:
```yaml
tools:
  - name: "my_custom_tool"
    enabled: true
    type: "custom"
    description: "My custom functionality"
    parameters: "param1,param2"
```

2. Implement the tool in your generated agent code:
```python
@function_tool
async def my_custom_tool(self, param1: str, param2: str):
    """Your custom tool implementation"""
    # Your logic here
    return f"Processed {param1} and {param2}"
```

### Modifying Agent Behavior
Edit the generated agent classes in `src/agents/` to customize:
- Personality and instructions
- Handoff logic
- Tool implementations
- Error handling

### Adding New Languages
1. Add language-specific text in your configuration
2. Update the generated agents to handle the new language
3. Modify greeting and response templates

## 📊 Monitoring and Analytics

### Webhook Integration
Your agent automatically sends events to configured webhooks:
```json
{
  "call_id": "unique-call-id",
  "event_type": "call_end",
  "conversation": [...],
  "handoffs": [...],
  "duration_seconds": 180,
  "workflow_type": "multi_agent"
}
```

### Conversation Tracking
All conversations are automatically tracked with:
- Agent transitions
- Tool usage
- User inputs
- Response times
- Error events

### Performance Metrics
Monitor your agent's performance:
- Average call duration
- Handoff frequency
- Task completion rates
- Error rates
- User satisfaction

## 🚀 Deployment Options

### LiveKit Cloud
```bash
# Deploy to LiveKit Cloud
livekit-cli deploy my-agent
```

### Docker Deployment
```dockerfile
FROM python:3.9-slim
COPY . /app
WORKDIR /app
RUN pip install -e .
CMD ["python", "agent.py", "start"]
```

### Serverless Deployment
Configure for AWS Lambda, Google Cloud Functions, or Azure Functions using the generated deployment configurations.

## 🛡️ Security Best Practices

### Environment Variables
- Never commit API keys to version control
- Use `.env` files for local development
- Use secure secret management in production

### Data Protection
- Enable PII detection for sensitive data
- Configure appropriate data retention periods
- Use HTTPS for all webhook endpoints

### Compliance
- Set `compliance_mode` for GDPR, HIPAA, etc.
- Enable consent tracking for recording
- Implement data deletion workflows

## 🐛 Troubleshooting

### Common Issues

#### Agent Won't Start
- Check API keys in `.env` file
- Verify LiveKit connection settings
- Check Python dependencies

#### Handoffs Not Working
- Verify agent configurations are enabled
- Check handoff trigger keywords
- Monitor conversation logs

#### Webhook Failures
- Verify webhook URL is accessible
- Check authentication headers
- Monitor webhook endpoint logs

### Debug Mode
Enable detailed logging:
```bash
LIVEKIT_LOG_LEVEL=debug python agent.py dev
```

### Testing
Run the generated test suite:
```bash
python -m pytest tests/ -v
```

## 📚 Next Steps

1. **Explore Examples**: Check the `/examples` directory for reference implementations
2. **Read API Docs**: Understand the generated code structure
3. **Join Community**: Connect with other LiveKit developers
4. **Contribute**: Add new features to the template system

## 🤝 Getting Help

- **Documentation**: Complete guides in `/docs`
- **GitHub Issues**: Report bugs and request features
- **LiveKit Community**: Join the Discord for support
- **Professional Support**: Enterprise support available

---

Ready to build amazing voice agents? Start with `make create-agent` and let the template do the work! 🚀