# Voice Agent Configuration Template

# INSTRUCTIONS FOR AI:
# Replace all {{VARIABLES}} with specific values based on user requirements
# Choose appropriate template from AI_AGENT_CREATOR_GUIDE.md
# Delete these instruction comments when generating final config

# === BASIC SETTINGS ===
language: "{{LANGUAGE}}"                          # "Svenska", "English", "Español", "Français"
voice: "{{VOICE}}"                                # See AI_AGENT_CREATOR_GUIDE.md for voice selection
workflow_type: "single_agent"
personality_traits: "{{PERSONALITY_TRAITS}}"      # e.g., "calm, professional, conversational, human-like"

# === GREETING MESSAGE ===
first_message: >
  {{FIRST_MESSAGE}}

use_prerecorded_greeting: false

# === AGENT CONFIGURATION ===
agents:
  primary:
    name: "{{AGENT_CLASS_NAME}}"                  # e.g., "MissedCallAgent", "ReservationAgent"
    personality: "{{PERSONALITY_TRAITS}}"
    specialization: "{{SPECIALIZATION}}"          # e.g., "call_intake_and_routing", "customer_service"
    voice: "{{VOICE}}"

# === WORKFLOW SETTINGS ===
workflow:
  context_preservation: true
  max_handoffs: 1

# === INFORMATION GATHERING ===
tasks:
  consent_collection:
    enabled: false
    required: false
  information_gathering:
    enabled: true
    required_fields: "name,phone"                 # Adjust based on needs

# === INTEGRATIONS ===
integrations:
  webhook:
    enabled: false                                # Set to true if you want call data sent to webhook
  telephony:
    transcription: true

# === OPENAI REALTIME CONFIGURATION ===
advanced:
  model_overrides:
    primary_model: "gpt-realtime"
    temperature: {{TEMPERATURE}}                  # 0.7-0.9, recommend 0.9 for natural conversation

# === MAIN SYSTEM PROMPT ===
prompt: |
  {{MAIN_SYSTEM_PROMPT}}

# ============================================================================
# TEMPLATE EXAMPLES - Choose one and fill in {{VARIABLES}}
# See AI_AGENT_CREATOR_GUIDE.md for complete templates and examples
# ============================================================================

# EXAMPLE 1: Missed Call Handler (Swedish Insurance Broker)
# language: "Svenska"
# voice: "marin"
# personality_traits: "calm, professional, conversational, human-like"
# temperature: 0.9
# first_message: >
#   Hej, tack för att du ringde. Jag är Roberts assistent. Hur kan jag hjälpa dig idag?
#
# prompt: |
#   Du är Roberts personliga assistent som svarar på HANS MISSADE SAMTAL.
#   Robert är försäkringsmäklare och kan inte svara just nu.
#
#   DITT HUVUDMÅL:
#   - Samla information om varför personen ringer
#   - Få deras namn och telefonnummer
#   - Säg att Robert kommer att ringa tillbaka
#   - FÖRSÖK INTE hjälpa med försäkringsfrågor - samla bara information
#   ...

# EXAMPLE 2: Restaurant Reservations (English)
# language: "English"
# voice: "shimmer"
# personality_traits: "friendly, efficient, hospitality-focused"
# temperature: 0.9
# first_message: >
#   Thank you for calling Bella Vista! How can I help you today?
#
# prompt: |
#   You are the reservation assistant for Bella Vista Italian Restaurant.
#
#   YOUR MAIN GOAL:
#   - Take reservation requests professionally
#   - Collect: name, phone, date, time, party size
#   - Confirm the reservation details clearly
#   - End with "We look forward to seeing you!"
#   ...

# EXAMPLE 3: Medical Office (English)
# language: "English"
# voice: "cedar"
# personality_traits: "calm, professional, empathetic, efficient"
# temperature: 0.8
# first_message: >
#   Thank you for calling Dr. Chen's office. How can I help you?
#
# prompt: |
#   You are the receptionist for Dr. Chen's dental practice.
#
#   YOUR MAIN GOAL:
#   - Determine if this is an emergency, urgent, or routine call
#   - Collect patient name and phone number
#   - For emergencies: tell them to call emergency dental line or 911
#   - For others: say someone will call back to schedule
#   ...
