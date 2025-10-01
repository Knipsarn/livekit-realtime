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

logger = logging.getLogger("robert-agent")


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
        # Simple Swedish system prompt like nils-dev
        system_prompt = """Du är Robert's professionella telefonassistent som svarar på vidarebefordrade samtal.

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

        super().__init__(instructions=system_prompt, tools=tools or [])
        self.session_ref = None
        self.ctx_ref = None

    def set_session_refs(self, session, ctx):
        """Store references for call ending"""
        self.session_ref = session
        self.ctx_ref = ctx


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

    logger.info(f"Starting Robert's agent for room: {tracker.call_id}")

    # Get voice from environment (like nils-dev)
    voice_name = os.getenv("VOICE_NAME", "marin")

    # Create AgentSession with GPT-Realtime exactly like working nils-dev
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            model="gpt-realtime",
            voice=voice_name,
            modalities=["audio", "text"],
            temperature=0.7,
            input_audio_transcription=InputAudioTranscription(
                model="whisper-1",
                language="sv",  # Swedish language
                prompt="Svenska konversation med AI-assistent Robert"
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

    # Send automatic Swedish greeting (exactly like nils-dev)
    greeting_message = "Hej, tack för att du ringde. Jag är Robert's assistent. Hur kan jag hjälpa dig idag?"
    await session.generate_reply(
        instructions=f"Säg hälsningen på svenska: '{greeting_message}' och vänta på svar."
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))