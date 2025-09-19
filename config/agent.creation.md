# 🤖 Agent Creation Template
# This file contains all configurable variables for creating LiveKit voice agents
# Replace all {{VARIABLE}} placeholders with your specific values

# === AGENT IDENTITY ===
title: "{{AGENT_TITLE}}"
description: "{{AGENT_DESCRIPTION}}"

# Primary agent configuration
agent_name: "{{AGENT_NAME}}"                     # e.g., "Jim", "Elsa", "Alex", "CustomerService"
owner_name: "{{OWNER_NAME}}"                     # e.g., "Samuel", "Acme Corp", "Healthcare Clinic"
language: "{{LANGUAGE}}"                         # e.g., "Svenska", "English", "Español"
voice: "{{VOICE}}"                              # e.g., "cedar", "nova", "marin", "alloy"

# === WORKFLOW CONFIGURATION ===
workflow_type: "{{WORKFLOW_TYPE}}"               # single_agent, multi_agent, task_based, hybrid

# Complexity and features
complexity_level: "{{COMPLEXITY}}"               # simple, intermediate, advanced, enterprise
use_workflows: {{USE_WORKFLOWS}}                 # true/false - Enable multi-agent workflows
use_tasks: {{USE_TASKS}}                         # true/false - Enable structured tasks
state_management: {{STATE_MANAGEMENT}}           # true/false - Track conversation state

# === BUSINESS CONTEXT ===
business_type: "{{BUSINESS_TYPE}}"               # personal, consulting, retail, healthcare, finance, legal
industry: "{{INDUSTRY}}"                        # technology, healthcare, finance, real_estate, other
use_case: "{{USE_CASE}}"                        # missed_calls, customer_support, sales, scheduling, triage

# Primary purpose and behavior
call_purpose: "{{CALL_PURPOSE}}"                # e.g., "missed call assistant", "customer support", "appointment booking"
personality_traits: "{{PERSONALITY}}"           # e.g., "friendly, professional, concise", "warm, empathetic, patient"
conversation_style: "{{STYLE}}"                 # formal, casual, consultative, medical, legal
response_length: "{{RESPONSE_LENGTH}}"          # short, medium, detailed

# === GREETING CONFIGURATION ===
first_message: >
  {{FIRST_MESSAGE}}

# Audio settings
use_prerecorded_greeting: {{USE_AUDIO}}          # true/false
audio_voice: "{{AUDIO_VOICE}}"                  # Voice for TTS generation (same as voice or different)
greeting_tone: "{{GREETING_TONE}}"              # professional, friendly, warm, energetic

# === WORKFLOW AGENTS ===
agents:
  primary:
    enabled: true
    name: "{{PRIMARY_AGENT_NAME}}"               # Main agent class name
    personality: "{{PRIMARY_PERSONALITY}}"       # Specific traits for primary agent
    specialization: "{{PRIMARY_SPEC}}"           # e.g., "general_support", "intake", "triage"
    voice: "{{PRIMARY_VOICE}}"                  # Voice for primary agent

  secondary:
    enabled: {{SECONDARY_ENABLED}}               # true/false
    name: "{{SECONDARY_AGENT_NAME}}"             # e.g., "TechnicalSupport", "BillingAgent"
    personality: "{{SECONDARY_PERSONALITY}}"     # Traits for secondary agent
    specialization: "{{SECONDARY_SPEC}}"         # e.g., "technical_issues", "billing_inquiries"
    voice: "{{SECONDARY_VOICE}}"                # Voice for secondary agent

  escalation:
    enabled: {{ESCALATION_ENABLED}}              # true/false
    name: "{{ESCALATION_AGENT_NAME}}"            # e.g., "Manager", "SpecialistSupervisor"
    personality: "{{ESCALATION_PERSONALITY}}"    # Traits for escalation agent
    specialization: "{{ESCALATION_SPEC}}"        # e.g., "complex_issues", "complaints"
    voice: "{{ESCALATION_VOICE}}"               # Voice for escalation agent

# === WORKFLOW RULES ===
workflow:
  handoff_triggers: "{{HANDOFF_RULES}}"          # keyword_based, intent_based, tool_based, manual
  context_preservation: {{PRESERVE_CONTEXT}}     # true/false - Maintain chat history across agents
  state_tracking: {{TRACK_STATE}}                # true/false - Track custom state data
  max_handoffs: {{MAX_HANDOFFS}}                 # Maximum number of agent handoffs per call

  # Handoff conditions
  handoff_keywords: "{{HANDOFF_KEYWORDS}}"       # e.g., "technical,billing,manager,escalate"
  auto_escalation: {{AUTO_ESCALATION}}           # true/false - Auto escalate on keywords

# === TASK CONFIGURATION ===
tasks:
  consent_collection:
    enabled: {{CONSENT_ENABLED}}                 # true/false
    required: {{CONSENT_REQUIRED}}               # true/false - Block call if declined
    message: "{{CONSENT_MESSAGE}}"               # Custom consent request message

  information_gathering:
    enabled: {{INFO_GATHERING_ENABLED}}          # true/false
    required_fields: "{{REQUIRED_FIELDS}}"       # name,email,phone,purpose,company
    optional_fields: "{{OPTIONAL_FIELDS}}"       # address,notes,callback_time
    validation_strict: {{STRICT_VALIDATION}}     # true/false

  appointment_scheduling:
    enabled: {{SCHEDULING_ENABLED}}              # true/false
    auto_suggest_times: {{AUTO_SUGGEST}}         # true/false
    buffer_minutes: {{BUFFER_MINUTES}}           # Minutes between appointments

  note_taking:
    enabled: {{NOTE_TAKING_ENABLED}}             # true/false
    auto_summarize: {{AUTO_SUMMARIZE}}           # true/false
    urgency_detection: {{URGENCY_DETECTION}}     # true/false

# === INTEGRATION CONFIGURATION ===
integrations:
  calendar:
    enabled: {{CALENDAR_ENABLED}}                # true/false
    provider: "{{CALENDAR_PROVIDER}}"            # google, outlook, caldav, custom
    timezone: "{{TIMEZONE}}"                     # e.g., "Europe/Stockholm", "America/New_York"

  crm:
    enabled: {{CRM_ENABLED}}                     # true/false
    provider: "{{CRM_PROVIDER}}"                 # salesforce, hubspot, pipedrive, custom
    auto_create_contacts: {{AUTO_CREATE_CRM}}    # true/false

  webhook:
    enabled: {{WEBHOOK_ENABLED}}                 # true/false
    url: "{{WEBHOOK_URL}}"                       # Webhook endpoint URL
    events: "{{WEBHOOK_EVENTS}}"                 # call_start,call_end,booking,note
    auth_header: "{{WEBHOOK_AUTH}}"              # Authorization header

  telephony:
    provider: "{{TELEPHONY_PROVIDER}}"           # telnyx, twilio, livekit
    recording: {{RECORDING_ENABLED}}             # true/false
    transcription: {{TRANSCRIPTION_ENABLED}}     # true/false

  email:
    enabled: {{EMAIL_ENABLED}}                   # true/false
    provider: "{{EMAIL_PROVIDER}}"               # smtp, sendgrid, mailgun
    auto_send_summaries: {{AUTO_EMAIL}}          # true/false

# === CUSTOM TOOLS ===
tools:
  - name: "{{TOOL_1_NAME}}"                      # e.g., "calendar_booking"
    enabled: {{TOOL_1_ENABLED}}                  # true/false
    type: "{{TOOL_1_TYPE}}"                      # booking, logging, transfer, search, custom
    description: "{{TOOL_1_DESCRIPTION}}"        # Tool description for LLM
    parameters: "{{TOOL_1_PARAMS}}"              # Required parameters

  - name: "{{TOOL_2_NAME}}"                      # e.g., "log_note"
    enabled: {{TOOL_2_ENABLED}}                  # true/false
    type: "{{TOOL_2_TYPE}}"                      # booking, logging, transfer, search, custom
    description: "{{TOOL_2_DESCRIPTION}}"        # Tool description for LLM
    parameters: "{{TOOL_2_PARAMS}}"              # Required parameters

  - name: "{{TOOL_3_NAME}}"                      # e.g., "transfer_to_human"
    enabled: {{TOOL_3_ENABLED}}                  # true/false
    type: "{{TOOL_3_TYPE}}"                      # booking, logging, transfer, search, custom
    description: "{{TOOL_3_DESCRIPTION}}"        # Tool description for LLM
    parameters: "{{TOOL_3_PARAMS}}"              # Required parameters

# === ADVANCED CONFIGURATION ===
advanced:
  # Model settings
  model_overrides:
    primary_model: "{{PRIMARY_MODEL}}"           # gpt-realtime, gpt-4o-realtime-preview
    fallback_model: "{{FALLBACK_MODEL}}"         # Fallback if primary fails
    temperature: {{LLM_TEMPERATURE}}             # 0.1-1.0
    max_tokens: {{MAX_TOKENS}}                   # Maximum response tokens

  # Voice and audio settings
  voice_settings:
    vad_threshold: {{VAD_THRESHOLD}}             # Voice activity detection threshold (0.1-1.0)
    vad_prefix_ms: {{VAD_PREFIX_MS}}             # Milliseconds before speech
    vad_silence_ms: {{VAD_SILENCE_MS}}           # Silence timeout in milliseconds

  audio:
    sample_rate: {{SAMPLE_RATE}}                 # Audio sample rate (16000, 24000, 48000)
    use_prerecorded: {{USE_PRERECORDED}}         # true/false
    audio_quality: "{{AUDIO_QUALITY}}"           # standard, hd
    enable_interruption: {{ENABLE_INTERRUPTION}} # true/false

  # Security and compliance
  security:
    enable_consent_tracking: {{CONSENT_TRACKING}} # true/false
    data_retention_days: {{DATA_RETENTION}}      # Days to retain conversation data
    pii_detection: {{PII_DETECTION}}             # true/false
    compliance_mode: "{{COMPLIANCE}}"            # none, gdpr, hipaa, sox

  # Performance tuning
  performance:
    max_call_duration: {{MAX_DURATION}}          # Maximum call duration in seconds
    response_timeout: {{RESPONSE_TIMEOUT}}       # Response timeout in seconds
    retry_attempts: {{RETRY_ATTEMPTS}}           # Number of retry attempts
    enable_caching: {{ENABLE_CACHING}}           # true/false

# === PROMPT CONFIGURATION ===
prompt: |
  {{MAIN_PROMPT}}

# === CONVERSATION EXAMPLES ===
examples:
  example_1:
    title: "{{EXAMPLE_1_TITLE}}"
    scenario: "{{EXAMPLE_1_SCENARIO}}"
    conversation: |
      {{EXAMPLE_1_CONVERSATION}}

  example_2:
    title: "{{EXAMPLE_2_TITLE}}"
    scenario: "{{EXAMPLE_2_SCENARIO}}"
    conversation: |
      {{EXAMPLE_2_CONVERSATION}}

# === DEPLOYMENT CONFIGURATION ===
deployment:
  environment: "{{ENVIRONMENT}}"                 # development, staging, production
  region: "{{DEPLOYMENT_REGION}}"               # us-east-1, eu-west-1, ap-southeast-1
  scaling: "{{SCALING_MODE}}"                    # manual, auto, serverless
  monitoring: {{ENABLE_MONITORING}}             # true/false

# === TESTING CONFIGURATION ===
testing:
  enable_test_suite: {{ENABLE_TESTING}}         # true/false
  test_scenarios: "{{TEST_SCENARIOS}}"          # basic, comprehensive, stress
  mock_integrations: {{MOCK_INTEGRATIONS}}      # true/false for testing

# === DOCUMENTATION ===
documentation:
  generate_readme: {{GENERATE_README}}          # true/false
  include_examples: {{INCLUDE_EXAMPLES}}        # true/false
  api_documentation: {{API_DOCS}}               # true/false