import asyncio
import logging
import os
from livekit import agents
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import AgentSession, Agent
from livekit.plugins import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger("voice-agent")


class VoiceAssistant(Agent):
    def __init__(self):
        super().__init__(
            instructions="You are a helpful voice assistant. Be conversational and friendly. Keep responses concise and natural for spoken conversation. You are speaking to someone over the phone, so be clear and engaging."
        )


async def entrypoint(ctx: JobContext):
    """Main entrypoint for the voice agent."""
    await ctx.connect()

    # Get configuration from environment
    voice_name = os.getenv("VOICE_NAME", "marin")

    # Create AgentSession with GPT-Realtime (2025 model)
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            model="gpt-realtime",  # Correct 2025 GPT-Realtime model
            voice=voice_name,
            modalities=["audio", "text"],
            temperature=0.7,
        )
    )

    # Start the session with the agent
    await session.start(
        room=ctx.room,
        agent=VoiceAssistant()
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))