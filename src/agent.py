import asyncio
import logging
import os
import time
import aiohttp
import wave
from datetime import datetime
from livekit import agents, api, rtc
from livekit.agents import JobContext, WorkerOptions, cli, get_job_context
from livekit.agents.voice import AgentSession, Agent
from livekit.agents import ConversationItemAddedEvent, UserInputTranscribedEvent, function_tool
from livekit.plugins import openai
from openai.types.beta.realtime.session import InputAudioTranscription
from dotenv import load_dotenv
import yaml

# Load environment variables
load_dotenv(".env.local")
load_dotenv()

logger = logging.getLogger("robert-agent")


def load_config():
    """Load configuration from robert-agent-config.md"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "robert-agent-config.md")

    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Extract YAML content (skip markdown comments)
        yaml_lines = []
        in_yaml = False

        for line in content.split('\n'):
            if line.strip().startswith('#') and not line.strip().startswith('# ==='):
                continue
            if line.strip() and not line.startswith('#'):
                in_yaml = True
            if in_yaml:
                yaml_lines.append(line)

        yaml_content = '\n'.join(yaml_lines)
        config = yaml.safe_load(yaml_content)
        logger.info(f"Loaded agent configuration from {config_path}")
        return config or {}

    except Exception as e:
        logger.warning(f"Could not load agent config from {config_path}: {e}")
        return {}


class ConversationTracker:
    def __init__(self):
        self.conversation_data = []
        self.start_time = time.time()
        self.call_id = None

    def add_item(self, role, content, timestamp=None):
        self.conversation_data.append({
            "role": role,
            "content": content,
            "timestamp": timestamp or time.time(),
            "datetime": datetime.now().isoformat()
        })

    def get_duration(self):
        return time.time() - self.start_time


class CallMemory:
    """Tracks collected information during the call"""
    def __init__(self):
        self.caller_name = None
        self.caller_phone = None
        self.caller_email = None
        self.call_purpose = None
        self.call_urgency = "normal"
        self.additional_info = []

    def get_summary(self):
        """Get current collected info as string for AI context"""
        info = []
        if self.caller_name:
            info.append(f"Namn: {self.caller_name}")
        if self.caller_phone:
            info.append(f"Telefon: {self.caller_phone}")
        if self.caller_email:
            info.append(f"E-post: {self.caller_email}")
        if self.call_purpose:
            info.append(f"Ärende: {self.call_purpose}")
        if self.additional_info:
            info.append(f"Detaljer: {', '.join(self.additional_info)}")

        return " | ".join(info) if info else "Ingen information insamlad än"


class VoiceAssistant(Agent):
    def __init__(self, config, tools=None):
        # Initialize memory for this call
        self.call_memory = CallMemory()

        # Call safety tracking
        self.call_start_time = time.time()
        self.last_activity_time = time.time()
        self.max_call_duration = 600  # 10 minutes
        self.inactivity_timeout = 30  # 30 seconds
        self.safety_monitor_task = None

        # Use custom prompt from config or fallback
        if config.get("prompt"):
            base_prompt = config["prompt"]
        else:
            # Fallback Swedish system prompt
            base_prompt = """Du är Robert's professionella telefonassistent som svarar på vidarebefordrade samtal.

GRUNDPRINCIPER:
- Ställ EN fråga i taget - aldrig flera frågor samtidigt
- Korta, tydliga meningar (max ~15 ord per fråga)
- Lugn, professionell, samtalslik ton
- Använd fyllnadsord ibland ("okej," "hm," "jag förstår") för naturlighet
- Upprepa alltid namn, nummer och e-post för att bekräfta riktighet

SAMTALSFLÖDE:
1. HÄLSNING: Erkänn vem du är (digital assistent)
2. IDENTIFIERA OCH KATEGORISERA: Lyssna och klassificera ärendet
3. SAMLA KONTAKTUPPGIFTER: Få namn och bekräfta telefon
4. ESKALERING: Föreslå att en kollega kontaktar dem
5. AVSLUTNING: Sammanfatta och avsluta artigt

Svara ALLTID på svenska och följ "en fråga i taget" principen."""

        # Use the base prompt - memory system kept internal for now
        system_prompt = base_prompt

        # Keep memory system but don't register as function tools to avoid conflicts
        # Memory data will be preserved but not exposed as AI tools yet
        all_tools = tools or []

        super().__init__(instructions=system_prompt, tools=all_tools)
        self.session_ref = None
        self.ctx_ref = None
        self.config = config

    def set_session_refs(self, session, ctx):
        """Store references for call ending"""
        self.session_ref = session
        self.ctx_ref = ctx

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity_time = time.time()

    async def start_safety_monitor(self):
        """Start background task to monitor call safety"""
        async def safety_monitor():
            while True:
                try:
                    current_time = time.time()

                    # Check maximum call duration (10 minutes)
                    if current_time - self.call_start_time > self.max_call_duration:
                        logger.warning(f"Call exceeded maximum duration ({self.max_call_duration}s), terminating")
                        await self.end_call_gracefully()
                        break

                    # Check inactivity timeout (30 seconds)
                    if current_time - self.last_activity_time > self.inactivity_timeout:
                        logger.warning(f"Call inactive for {self.inactivity_timeout}s, terminating")
                        await self.end_call_gracefully()
                        break

                    # Check every 5 seconds
                    await asyncio.sleep(5)

                except Exception as e:
                    logger.error(f"Safety monitor error: {e}")
                    break

        self.safety_monitor_task = asyncio.create_task(safety_monitor())
        logger.info("Call safety monitor started")

    @function_tool
    async def save_caller_info(self, name: str = None, phone: str = None, email: str = None, purpose: str = None, urgency: str = "normal"):
        """Save caller information to memory. Use this immediately when you learn any info about the caller."""
        # Update activity when user provides information
        self.update_activity()
        if name:
            self.call_memory.caller_name = name
            logger.info(f"Saved caller name: {name}")
        if phone:
            self.call_memory.caller_phone = phone
            logger.info(f"Saved caller phone: {phone}")
        if email:
            self.call_memory.caller_email = email
            logger.info(f"Saved caller email: {email}")
        if purpose:
            self.call_memory.call_purpose = purpose
            logger.info(f"Saved call purpose: {purpose}")
        if urgency:
            self.call_memory.call_urgency = urgency

        return f"Sparad information: {self.call_memory.get_summary()}"

    @function_tool
    async def check_caller_memory(self):
        """Check what information has already been collected. Use this before asking for any information."""
        summary = self.call_memory.get_summary()
        logger.info(f"Retrieved memory: {summary}")
        return summary

    @function_tool
    async def save_call_details(self, details: str):
        """Add additional details about the call or issue."""
        # Update activity when user provides information
        self.update_activity()
        self.call_memory.additional_info.append(details)
        logger.info(f"Added call details: {details}")
        return f"Detaljer tillagda: {details}"

    async def end_call_gracefully(self):
        """Programmatically end the call with proper cleanup for telephony"""
        try:
            # Stop safety monitor
            if self.safety_monitor_task:
                self.safety_monitor_task.cancel()
                logger.info("Safety monitor stopped")
            if self.session_ref:
                logger.info("Generating farewell message...")
                speech_handle = await self.session_ref.generate_reply(
                    instructions="Säg hejdå på svenska och avsluta samtalet vänligt."
                )

                # CRITICAL: Wait for speech to complete with timeout
                await asyncio.wait_for(speech_handle.wait(), timeout=10.0)
                logger.info("Farewell message completed")

                # Small delay to ensure audio transmission completes
                await asyncio.sleep(1.0)

            # Delete room for complete call termination (required for telephony)
            ctx = get_job_context()
            if ctx:
                logger.info(f"Deleting room: {ctx.room.name}")
                await ctx.api.room.delete_room(
                    api.DeleteRoomRequest(room=ctx.room.name)
                )
                logger.info("Room deleted successfully - call terminated")
            else:
                logger.warning("No job context available for room deletion")

        except asyncio.TimeoutError:
            logger.warning("Farewell message timed out, force terminating")
            ctx = get_job_context()
            if ctx:
                await ctx.api.room.delete_room(
                    api.DeleteRoomRequest(room=ctx.room.name)
                )
        except Exception as e:
            logger.error(f"Error during call termination: {e}")
            # Ensure call still ends even with errors
            try:
                ctx = get_job_context()
                if ctx:
                    await ctx.api.room.delete_room(
                        api.DeleteRoomRequest(room=ctx.room.name)
                    )
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup call: {cleanup_error}")


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


async def send_webhook(tracker: ConversationTracker):
    """Send conversation data to webhook after call completion"""
    webhook_url = os.getenv("WEBHOOK_URL")
    if not webhook_url:
        logger.info("No webhook URL configured, skipping webhook")
        return

    payload = {
        "call_id": tracker.call_id,
        "conversation": tracker.conversation_data,
        "duration_seconds": tracker.get_duration(),
        "timestamp": int(time.time()),
        "start_time": tracker.start_time,
        "end_time": time.time()
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    logger.info("Webhook sent successfully")
                else:
                    logger.error(f"Webhook failed: {response.status}")
    except Exception as e:
        logger.error(f"Webhook error: {e}")


async def entrypoint(ctx: JobContext):
    """Main entrypoint for the voice agent."""
    await ctx.connect()

    # Load configuration
    config = load_config()

    # Initialize conversation tracking
    tracker = ConversationTracker()
    tracker.call_id = ctx.room.name

    logger.info(f"Starting Robert's agent for room: {tracker.call_id}")

    # Get configuration values
    voice_name = config.get("voice", "cedar")
    language = config.get("language", "English")
    model_config = config.get("advanced", {}).get("model_overrides", {})

    logger.info(f"Using voice: {voice_name}, language: {language}")

    # Create AgentSession with GPT-Realtime and configuration from file
    logger.info(f"Creating session with voice: {voice_name}, model: {model_config.get('primary_model', 'gpt-realtime')}")

    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            model=model_config.get("primary_model", "gpt-realtime"),
            voice=voice_name,
            modalities=["audio", "text"],
            temperature=model_config.get("temperature", 0.7)
        )
    )

    logger.info("Session created successfully")

    # Event handlers for conversation tracking
    @session.on("conversation_item_added")
    def on_conversation_item_added(event: ConversationItemAddedEvent):
        tracker.add_item(
            role=event.item.role,
            content=event.item.text_content,
            timestamp=event.created_at
        )
        logger.info(f"Conversation item from {event.item.role}: {event.item.text_content[:50]}...")

        # Update activity when conversation happens
        if hasattr(session, '_agent_ref') and session._agent_ref:
            session._agent_ref.update_activity()

    @session.on("user_input_transcribed")
    def on_user_input_transcribed(event: UserInputTranscribedEvent):
        if event.is_final:
            logger.info(f"Final user transcript: {event.transcript}")
            # Update activity when user speaks
            if hasattr(session, '_agent_ref') and session._agent_ref:
                session._agent_ref.update_activity()

    # Participant disconnect detection
    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        logger.info(f"Participant disconnected: {participant.identity}")
        # If the caller (not agent) disconnects, stop safety monitor and end the call
        if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_STANDARD:
            logger.warning("Caller disconnected, stopping safety monitor")
            # Stop safety monitor immediately
            if agent.safety_monitor_task:
                agent.safety_monitor_task.cancel()
                logger.info("Safety monitor stopped due to participant disconnect")
            # The session will close automatically, no need to manually end call

    # Register webhook as shutdown callback
    async def send_completion_webhook():
        logger.info("Sending completion webhook...")
        await send_webhook(tracker)

    ctx.add_shutdown_callback(send_completion_webhook)

    # Extract caller phone number from room participants
    caller_phone = None
    for participant in ctx.room.remote_participants:
        if participant.identity.startswith("sip_"):
            caller_phone = participant.identity.replace("sip_", "")
            logger.info(f"Extracted caller phone: {caller_phone}")
            break

    # Create agent with configuration
    agent = VoiceAssistant(config, tools=[end_call])
    agent.set_session_refs(session, ctx)

    # Store caller phone number in memory if found
    if caller_phone:
        await agent.save_caller_info(phone=caller_phone)
        logger.info(f"Auto-stored caller phone: {caller_phone}")

    # Store agent reference in session for event handlers
    session._agent_ref = agent

    # Start safety monitoring
    await agent.start_safety_monitor()

    # Start the session with the agent and function tools
    await session.start(
        room=ctx.room,
        agent=agent
    )

    # Get first message from config or use default
    greeting_message = config.get("first_message", "Hej, tack för att du ringde. Jag är Robert's assistent. Hur kan jag hjälpa dig idag?")

    # Clean up multi-line YAML if needed
    if isinstance(greeting_message, str):
        greeting_message = greeting_message.strip().replace('\n', ' ')

    logger.info(f"Sending greeting: {greeting_message}")

    # Send greeting
    await asyncio.sleep(0.8)  # Small delay for audio pipeline
    greeting_handle = await session.generate_reply(
        instructions=f"Säg hälsningen på svenska: '{greeting_message}' och vänta på svar."
    )
    logger.info("Greeting sent successfully")


if __name__ == "__main__":
    # Only allow deployment entry point - no local dev CLI
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))