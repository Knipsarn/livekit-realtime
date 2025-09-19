import asyncio
import logging
import os
import time
import aiohttp
import yaml
import wave
from datetime import datetime
from livekit import agents, api, rtc
from livekit.agents import JobContext, WorkerOptions, cli, get_job_context
from livekit.agents.voice import AgentSession, Agent
from livekit.agents import ConversationItemAddedEvent, UserInputTranscribedEvent, function_tool
from livekit.plugins import openai
from openai.types.beta.realtime.session import InputAudioTranscription
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")
load_dotenv()

logger = logging.getLogger("voice-agent")


def load_agent_config():
    """Load agent configuration from samuel-agent.md"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "agents", "samuel-agent.md")

    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Parse the YAML content
        if content.startswith('title:'):
            # Look for the tools section to find end of main config
            tools_start = content.find('\ntools:')
            if tools_start != -1:
                yaml_content = content[:tools_start]
            else:
                yaml_content = content

            config = yaml.safe_load(yaml_content)
            print(f"YAML CONTENT: {yaml_content[:200]}...")
            print(f"PARSED CONFIG: {config}")
            logger.info(f"Loaded agent configuration from {config_path}")
            logger.info(f"Config keys: {list(config.keys()) if config else 'None'}")
            return config

    except Exception as e:
        logger.warning(f"Could not load agent config from {config_path}: {e}")
        return {}

# Load agent configuration (will be reloaded in entrypoint)
AGENT_CONFIG = {}


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


class VoiceAssistant(Agent):
    def __init__(self, tools=None):
        # Load system prompt from samuel-agent.md or use environment variable as fallback
        system_prompt = os.getenv("AGENT_SYSTEM_PROMPT")
        if not system_prompt and AGENT_CONFIG.get("prompt"):
            system_prompt = AGENT_CONFIG["prompt"]

        # Default fallback if neither file nor env has prompt
        if not system_prompt:
            system_prompt = "Du är en hjälpsam telefonassistent som tar meddelanden."

        super().__init__(instructions=system_prompt, tools=tools or [])
        self.session_ref = None
        self.ctx_ref = None

    def set_session_refs(self, session, ctx):
        """Store references for call ending"""
        self.session_ref = session
        self.ctx_ref = ctx

    async def end_call_gracefully(self):
        """Programmatically end the call with proper cleanup for telephony"""
        try:
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
async def calendar_booking(date_time: str, caller_name: str, phone: str, email: str = None, notes: str = None):
    """Boka en tid för att Samuel ska ringa upp eller för ett kort möte"""
    ctx = get_job_context()
    if ctx is None:
        return "Kunde inte boka tid - ingen kontext tillgänglig"

    # Log the booking details (in production, this would integrate with a real calendar system)
    booking_data = {
        "type": "calendar_booking",
        "date_time": date_time,
        "caller_name": caller_name,
        "phone": phone,
        "email": email,
        "notes": notes,
        "timestamp": datetime.now().isoformat()
    }

    logger.info(f"Calendar booking created: {booking_data}")

    # In production: integrate with Google Calendar, Outlook, or other calendar API
    # For now, we'll log it and it will be sent via webhook

    return "Toppen, jag har bokat tiden. Samuel återkommer enligt bokningen."


@function_tool
async def log_note(caller_name: str, phone: str, summary: str, urgency: str = "normal", type: str = "privat", email: str = None):
    """Spara sammanfattning av samtal för Samuel"""
    ctx = get_job_context()
    if ctx is None:
        return "Kunde inte spara anteckning - ingen kontext tillgänglig"

    # Log the note details
    note_data = {
        "type": "log_note",
        "caller_name": caller_name,
        "phone": phone,
        "email": email,
        "summary": summary,
        "urgency": urgency,
        "call_type": type,
        "timestamp": datetime.now().isoformat()
    }

    logger.info(f"Note logged: {note_data}")

    return "Anteckningen har sparats."


@function_tool
async def end_call():
    """Avsluta samtalet när konversationen är klar"""
    ctx = get_job_context()
    if ctx is None:
        return "Could not end call - no context available"

    logger.info("Function tool called to end call")
    await ctx.api.room.delete_room(
        api.DeleteRoomRequest(room=ctx.room.name)
    )
    return "Samtalet avslutas."


async def play_greeting_audio(ctx: JobContext):
    """Play pre-recorded greeting audio file and ensure it's recorded by Telnyx"""
    try:
        # Look for greeting audio file
        audio_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "greeting.wav")

        if not os.path.exists(audio_path):
            logger.warning(f"Greeting audio file not found at {audio_path}, falling back to AI voice")
            return False

        logger.info(f"Playing pre-recorded greeting from: {audio_path}")

        # Create audio source and track with proper sample rate for telephony
        audio_source = rtc.AudioSource(sample_rate=24000, num_channels=1)
        track = rtc.LocalAudioTrack.create_audio_track("greeting", audio_source)

        # Publish the track to room - this ensures Telnyx recording captures it
        publication = await ctx.room.local_participant.publish_track(track, rtc.TrackPublishOptions(
            name="greeting_audio"
        ))

        # Read and play the audio file
        with wave.open(audio_path, 'rb') as wav_file:
            sample_rate = wav_file.getframerate()
            num_channels = wav_file.getnchannels()
            frames = wav_file.readframes(wav_file.getnframes())

            # Calculate duration for proper timing
            duration = len(frames) / (sample_rate * num_channels * 2)  # 2 bytes per sample for 16-bit
            logger.info(f"Greeting audio duration: {duration:.2f} seconds")

            # Convert to AudioFrame with proper format
            audio_frame = rtc.AudioFrame(
                data=frames,
                sample_rate=sample_rate,
                num_channels=num_channels,
                samples_per_channel=len(frames) // (num_channels * 2)
            )

            # Send the audio frame to the room
            await audio_source.capture_frame(audio_frame)

            # Wait for audio to finish playing with extra buffer for network/processing
            await asyncio.sleep(duration + 0.5)

        # Keep track published briefly to ensure recording system captures it
        await asyncio.sleep(0.3)

        # Unpublish the track
        await ctx.room.local_participant.unpublish_track(publication.sid)
        logger.info(f"Greeting audio playback completed and track unpublished")
        return True

    except Exception as e:
        logger.error(f"Failed to play greeting audio: {e}")
        return False


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

    # Reload configuration for each call
    global AGENT_CONFIG
    AGENT_CONFIG = load_agent_config()

    # Initialize conversation tracking
    tracker = ConversationTracker()
    tracker.call_id = ctx.room.name

    logger.info(f"Starting call tracking for room: {tracker.call_id}")

    # Get configuration from samuel-agent.md or environment
    voice_name = os.getenv("VOICE_NAME")
    if not voice_name and AGENT_CONFIG.get("voice"):
        voice_name = AGENT_CONFIG["voice"]
    if not voice_name:
        voice_name = "cedar"  # Default fallback

    # Create AgentSession with GPT-Realtime (2025 model) and Swedish configuration
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            model="gpt-realtime",  # Correct 2025 GPT-Realtime model
            voice=voice_name,
            modalities=["audio", "text"],
            temperature=0.7,
            # Remove transcription config to avoid API errors
            # input_audio_transcription=InputAudioTranscription(
            #     model="whisper-1"
            # )
        )
    )

    # Event handlers for conversation tracking
    @session.on("conversation_item_added")
    def on_conversation_item_added(event: ConversationItemAddedEvent):
        tracker.add_item(
            role=event.item.role,
            content=event.item.text_content,
            timestamp=event.created_at
        )
        logger.info(f"Conversation item from {event.item.role}: {event.item.text_content[:50]}...")

    @session.on("user_input_transcribed")
    def on_user_input_transcribed(event: UserInputTranscribedEvent):
        if event.is_final:
            logger.info(f"Final user transcript: {event.transcript}")
            # Remove automatic word detection - let agent decide via function tools

    # Register webhook as shutdown callback
    async def send_completion_webhook():
        logger.info("Sending completion webhook...")
        await send_webhook(tracker)

    ctx.add_shutdown_callback(send_completion_webhook)

    # Create agent and set session references for call ending
    agent = VoiceAssistant(tools=[calendar_booking, log_note, end_call])
    agent.set_session_refs(session, ctx)

    # Start the session with the agent and function tools
    await session.start(
        room=ctx.room,
        agent=agent
    )

    # Send greeting from samuel-agent.md or environment
    greeting_message = os.getenv("AGENT_GREETING_MESSAGE")
    print(f"ENV GREETING: {greeting_message}")
    print(f"CONFIG FIRST_MESSAGE: {AGENT_CONFIG.get('first_message')}")

    if not greeting_message and AGENT_CONFIG.get("first_message"):
        greeting_message = AGENT_CONFIG["first_message"]
    if not greeting_message:
        greeting_message = "Hej, du har nått Samuel. Jag är Jim, hans assistent. Han kan inte svara just nu, men jag hjälper gärna till att ta ett meddelande. Vem pratar jag med?"

    print(f"FINAL GREETING: '{greeting_message}'")
    print(f"GREETING LENGTH: {len(greeting_message)}")
    print(f"GREETING REPR: {repr(greeting_message)}")

    instruction = f"Säg exakt denna hälsning: '{greeting_message}'"
    print(f"FULL INSTRUCTION: {instruction}")
    logger.info(f"Using greeting: {greeting_message[:100]}...")

    # Try to play recorded greeting audio file, fallback to AI voice
    audio_played = await play_greeting_audio(ctx)

    if not audio_played:
        # Fallback to AI voice greeting
        await asyncio.sleep(0.8)  # Small delay for audio pipeline
        await session.generate_reply(instructions=instruction)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))