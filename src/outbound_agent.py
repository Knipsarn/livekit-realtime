import asyncio
import logging
import os
import time
import aiohttp
import json
from datetime import datetime
from livekit import agents, api, rtc
from livekit.agents import JobContext, WorkerOptions, cli, get_job_context
from livekit.agents.voice import AgentSession, Agent
from livekit.agents import ConversationItemAddedEvent, UserInputTranscribedEvent, function_tool
from livekit.plugins import openai
from openai.types.beta.realtime.session import InputAudioTranscription
from google.protobuf.duration_pb2 import Duration
from dotenv import load_dotenv
import yaml

# Load environment variables
load_dotenv(".env.local")
load_dotenv(".env.outbound")
load_dotenv()

logger = logging.getLogger("outbound-agent")


def load_config():
    """Load configuration from outbound-agent-config.md"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outbound-agent-config.md")

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
        logger.info(f"Loaded outbound agent configuration from {config_path}")
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


class ProspectMemory:
    """Tracks collected information during the outbound call"""
    def __init__(self):
        self.prospect_name = None
        self.company_name = None
        self.contact_phone = None
        self.interest_level = None
        self.current_solution = None
        self.pain_points = []
        self.next_step = None
        self.meeting_booked = False
        self.info_sent = False

    def get_summary(self):
        """Get current collected info as string for AI context"""
        info = []
        if self.prospect_name:
            info.append(f"Kontakt: {self.prospect_name}")
        if self.company_name:
            info.append(f"Företag: {self.company_name}")
        if self.contact_phone:
            info.append(f"Telefon: {self.contact_phone}")
        if self.interest_level:
            info.append(f"Intresse: {self.interest_level}")
        if self.current_solution:
            info.append(f"Nuvarande lösning: {self.current_solution}")
        if self.pain_points:
            info.append(f"Problem: {', '.join(self.pain_points)}")
        if self.next_step:
            info.append(f"Nästa steg: {self.next_step}")

        return " | ".join(info) if info else "Ingen information insamlad än"


class OutboundVoiceAgent(Agent):
    def __init__(self, config, tools=None):
        # Initialize memory for this call
        self.prospect_memory = ProspectMemory()

        # Call safety tracking (same as robert-demo)
        self.call_start_time = time.time()
        self.last_activity_time = time.time()
        self.max_call_duration = 600  # 10 minutes
        self.inactivity_timeout = 30  # 30 seconds
        self.safety_monitor_task = None

        # Use custom prompt from config or fallback
        if config.get("prompt"):
            base_prompt = config["prompt"]
        else:
            # Fallback outbound system prompt
            base_prompt = """Du är Nils AI och du ringer till personer som har fyllt i ett intresseformulär.

FÖRSTA HANDLING: Säg hälsningen "Hej det är Finn, tack för ditt intresse i vår produkt. Har du en minut över?" och vänta på svar.

Ditt mål är att kvalificera deras intresse och erbjuda nästa steg (möte eller information)."""

        system_prompt = base_prompt
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
        logger.info("Outbound call safety monitor started")

    @function_tool
    async def save_prospect_info(self, name: str = None, company: str = None, phone: str = None,
                                interest_level: str = None, current_solution: str = None):
        """Save prospect information to memory. Use this when you learn about the prospect."""
        self.update_activity()

        if name:
            self.prospect_memory.prospect_name = name
            logger.info(f"Saved prospect name: {name}")
        if company:
            self.prospect_memory.company_name = company
            logger.info(f"Saved company: {company}")
        if phone:
            self.prospect_memory.contact_phone = phone
            logger.info(f"Saved phone: {phone}")
        if interest_level:
            self.prospect_memory.interest_level = interest_level
            logger.info(f"Saved interest level: {interest_level}")
        if current_solution:
            self.prospect_memory.current_solution = current_solution
            logger.info(f"Saved current solution: {current_solution}")

        return f"Sparad information: {self.prospect_memory.get_summary()}"

    @function_tool
    async def check_prospect_memory(self):
        """Check what information has already been collected about the prospect."""
        summary = self.prospect_memory.get_summary()
        logger.info(f"Retrieved prospect memory: {summary}")
        return summary

    @function_tool
    async def save_pain_points(self, pain_point: str):
        """Save identified pain points or challenges."""
        self.update_activity()
        self.prospect_memory.pain_points.append(pain_point)
        logger.info(f"Added pain point: {pain_point}")
        return f"Problem identifierat: {pain_point}"

    @function_tool
    async def book_meeting(self, meeting_time: str = "nästa vecka"):
        """Book a meeting with Nils for the prospect."""
        self.update_activity()
        self.prospect_memory.meeting_booked = True
        self.prospect_memory.next_step = f"Möte bokat för {meeting_time}"
        logger.info(f"Meeting booked: {meeting_time}")
        return f"Möte bokat för {meeting_time} - kalenderinbjudan skickas"

    @function_tool
    async def send_information(self, info_type: str = "produktinformation"):
        """Send product information to the prospect."""
        self.update_activity()
        self.prospect_memory.info_sent = True
        self.prospect_memory.next_step = f"Skickar {info_type}"
        logger.info(f"Information sent: {info_type}")
        return f"{info_type} skickas via SMS/email"

    async def end_call_gracefully(self):
        """Programmatically end the call with proper cleanup"""
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

                # Wait for speech to complete with timeout
                await asyncio.wait_for(speech_handle.wait(), timeout=10.0)
                logger.info("Farewell message completed")

                # Small delay to ensure audio transmission completes
                await asyncio.sleep(1.0)

            # Delete room for complete call termination
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
    """Main entrypoint for the outbound voice agent."""
    await ctx.connect()

    # Load configuration
    config = load_config()

    # Check for outbound call metadata
    metadata = ""

    # Try multiple ways to access dispatch metadata
    if hasattr(ctx.job, 'metadata') and ctx.job.metadata:
        metadata = ctx.job.metadata
        logger.info(f"🔍 FOUND metadata via job.metadata: {metadata}")
    elif hasattr(ctx.job, 'dispatch_metadata') and ctx.job.dispatch_metadata:
        metadata = ctx.job.dispatch_metadata
        logger.info(f"🔍 FOUND metadata via job.dispatch_metadata: {metadata}")
    elif hasattr(ctx.room, 'metadata') and ctx.room.metadata:
        metadata = ctx.room.metadata
        logger.info(f"🔍 FOUND metadata via room.metadata: {metadata}")
    elif "outbound-call" in ctx.room.name or "outbound-test" in ctx.room.name:
        # Workaround for metadata issues
        metadata = '{"phone_number": "+46723161614"}'
        logger.info(f"🔍 DETECTED outbound room via name pattern: {metadata}")

    # Check if this is an outbound call
    is_outbound = bool(metadata)
    logger.info(f"🔍 OUTBOUND DEBUG: is_outbound={is_outbound}, metadata={metadata}")

    if is_outbound:
        try:
            dial_info = json.loads(metadata)
            phone_number = dial_info["phone_number"]
            outbound_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID", "ST_SigM7KTZGNok")
            logger.info(f"🔍 OUTBOUND SETUP: phone={phone_number}, trunk_id={outbound_trunk_id}")

            # Create SIP participant for outbound call
            logger.info("📞 Creating outbound SIP participant...")
            result = await ctx.api.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(
                    room_name=ctx.room.name,
                    sip_trunk_id=outbound_trunk_id,
                    sip_call_to=phone_number,
                    participant_identity=phone_number,
                    max_call_duration=Duration(seconds=600),  # 10 minute limit
                    ringing_timeout=Duration(seconds=30),     # 30s to answer
                    wait_until_answered=True
                )
            )

            # Emergency cleanup as backup
            async def emergency_cleanup():
                await asyncio.sleep(660)  # 11 minutes backup
                try:
                    await ctx.api.room.delete_room(api.DeleteRoomRequest(room=ctx.room.name))
                    logger.warning("⚠️ Emergency cleanup executed - 10 minute limit reached")
                except:
                    pass

            asyncio.create_task(emergency_cleanup())
            logger.info(f"✅ SIP participant created: {result}")

        except Exception as e:
            error_msg = f"❌ Outbound call failed: {e}"
            logger.error(error_msg)
            return  # Exit if outbound call fails

    # Initialize conversation tracking
    tracker = ConversationTracker()
    tracker.call_id = ctx.room.name
    logger.info(f"Starting outbound agent for room: {tracker.call_id}")

    # Get configuration values
    voice_name = config.get("voice", "marin")
    language = config.get("language", "Svenska")
    model_config = config.get("advanced", {}).get("model_overrides", {})

    logger.info(f"Using voice: {voice_name}, language: {language}")

    # Create AgentSession with GPT-Realtime and configuration
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            model=model_config.get("primary_model", "gpt-realtime"),
            voice=voice_name,
            modalities=["audio", "text"],
            temperature=model_config.get("temperature", 0.6),
            # Optimized for outbound calls
            input_audio_transcription=InputAudioTranscription(
                model="whisper-1",
                language="sv",
                prompt="Svenska röstsamtal, outbound försäljning"
            )
        ),
        # Anti-lag optimizations
        min_endpointing_delay=0.25,
        allow_interruptions=True,
        min_interruption_duration=0.3
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
        if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
            logger.warning("Prospect disconnected, stopping safety monitor")
            if hasattr(agent, 'safety_monitor_task') and agent.safety_monitor_task:
                agent.safety_monitor_task.cancel()
                logger.info("Safety monitor stopped due to participant disconnect")

    # Register webhook as shutdown callback
    async def send_completion_webhook():
        logger.info("Sending completion webhook...")
        await send_webhook(tracker)

    ctx.add_shutdown_callback(send_completion_webhook)

    # Create outbound agent with configuration
    agent = OutboundVoiceAgent(config, tools=[end_call])
    agent.set_session_refs(session, ctx)

    # Store prospect phone number from metadata
    if is_outbound and metadata:
        try:
            dial_info = json.loads(metadata)
            prospect_phone = dial_info["phone_number"]
            await agent.save_prospect_info(phone=prospect_phone)
            logger.info(f"Auto-stored prospect phone: {prospect_phone}")
        except:
            pass

    # Store agent reference in session for event handlers
    session._agent_ref = agent

    # Start safety monitoring
    await agent.start_safety_monitor()

    # Start the session with the agent
    await session.start(
        room=ctx.room,
        agent=agent
    )

    # Wait for participant to join (outbound calls)
    if is_outbound:
        logger.info("🎤 Setting up outbound greeting delivery...")

        # Track if greeting has been delivered
        greeting_delivered = False

        # Check for existing participants (if call already connected)
        async def check_existing_participants():
            await asyncio.sleep(0.5)
            participants = list(ctx.room.remote_participants.values())
            logger.info(f"🔍 Found {len(participants)} remote participants")

            for participant in participants:
                if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
                    call_status = participant.attributes.get("sip.callStatus", "unknown")
                    logger.info(f"🔍 SIP participant {participant.identity} status: {call_status}")

                    if call_status == "active" and not greeting_delivered:
                        logger.info("🎯 SIP participant is ACTIVE - delivering greeting...")
                        asyncio.create_task(deliver_greeting())

        # Event handler for when participant joins
        @ctx.room.on("participant_connected")
        def on_participant_joins(participant: rtc.RemoteParticipant):
            nonlocal greeting_delivered
            if (participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP and
                not greeting_delivered):
                logger.info(f"🎯 PROSPECT ANSWERED - participant {participant.identity} joined")
                greeting_delivered = True
                asyncio.create_task(deliver_greeting())

        async def deliver_greeting():
            nonlocal greeting_delivered
            if greeting_delivered:
                return
            greeting_delivered = True

            try:
                # Get first message from config or use default
                greeting_message = config.get("first_message",
                    "Hej det är Finn, tack för ditt intresse i vår produkt. Har du en minut över?")

                # Clean up multi-line YAML if needed
                if isinstance(greeting_message, str):
                    greeting_message = greeting_message.strip().replace('\n', ' ')

                logger.info(f"🎯 Delivering outbound greeting: {greeting_message}")
                await session.generate_reply(
                    instructions=f"Säg hälsningen på svenska: '{greeting_message}' och vänta på svar."
                )
                logger.info("✅ Outbound greeting delivered successfully")
            except Exception as e:
                logger.error(f"❌ Outbound greeting failed: {e}")

        # Check for existing participants
        asyncio.create_task(check_existing_participants())


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))