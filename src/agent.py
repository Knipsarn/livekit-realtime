import asyncio
import logging
import os
import time
import aiohttp
from datetime import datetime
from livekit import agents, api
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
        # Load system prompt from environment with Swedish fallback
        system_prompt = os.getenv("AGENT_SYSTEM_PROMPT",
            "Du är en hjälpsam röstassistent som ALLTID svarar på svenska. "
            "Var konversationell och vänlig. Håll svaren korta och naturliga för talade konversationer. "
            "Du pratar med någon över telefon, så var tydlig och engagerande. "
            "Svara ALLTID på svenska, oavsett vilket språk användaren pratar."
        )
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
                    instructions="Säg adjö på svenska: 'Tack för samtalet! Ha en bra dag. Vi hörs!' och avsluta samtalet."
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

    # Initialize conversation tracking
    tracker = ConversationTracker()
    tracker.call_id = ctx.room.name

    logger.info(f"Starting call tracking for room: {tracker.call_id}")

    # Get configuration from environment
    voice_name = os.getenv("VOICE_NAME", "marin")

    # Create AgentSession with GPT-Realtime (2025 model) and Swedish configuration
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            model="gpt-realtime",  # Correct 2025 GPT-Realtime model
            voice=voice_name,
            modalities=["audio", "text"],
            temperature=0.7,
            input_audio_transcription=InputAudioTranscription(
                model="whisper-1",
                language="sv",  # Swedish language
                prompt="Svenska konversation med AI-assistent Elsa"
            )
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
    agent = VoiceAssistant(tools=[end_call])
    agent.set_session_refs(session, ctx)

    # Start the session with the agent and function tools
    await session.start(
        room=ctx.room,
        agent=agent
    )

    # Send automatic Swedish greeting
    greeting_message = os.getenv("AGENT_GREETING_MESSAGE", "Hej och välkommen! Jag är Elsa, din AI-assistent. Vad kan jag hjälpa dig med idag?")
    await session.generate_reply(
        instructions=f"Säg hälsningen på svenska: '{greeting_message}' och vänta på svar."
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))