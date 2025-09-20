"""
Robert's Conversational Workflow - Simplified working version
Based on samuel-dev working pattern
"""

import asyncio
import logging
import os
import time
from datetime import datetime
from livekit import agents, api
from livekit.agents import JobContext, WorkerOptions, cli, get_job_context
from livekit.agents.voice import AgentSession, Agent
from livekit.agents import ConversationItemAddedEvent, UserInputTranscribedEvent
from livekit.plugins import openai
from openai.types.beta.realtime.session import InputAudioTranscription
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger("robert-workflow")


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


class RobertAgent(Agent):
    def __init__(self):
        # Robert's Swedish system prompt with natural conversation rules
        system_prompt = """Du är Robert's professionella telefonassistent som svarar på vidarebefordrade samtal.

GRUNDPRINCIPER:
- Ställ EN fråga i taget - aldrig flera frågor samtidigt
- Korta, tydliga meningar (max ~15 ord per fråga)
- Lugn, professionell, samtalslik ton
- Använd fyllnadsord ibland ("okej," "hm," "jag förstår") för naturlighet
- Upprepa alltid namn, nummer och e-post för att bekräfta riktighet
- Ställ alltid följdfrågor på ett vägledande sätt, inte skriptad upprepning

SAMTALSFLÖDE:
1. HÄLSNING: Erkänn vem du är (digital assistent)
2. IDENTIFIERA OCH KATEGORISERA: Lyssna och klassificera ärendet
   - Om vagt: ställ en förtydligande fråga
   - Om tydligt: ställ en kort följdfråga inom kategorin
3. SAMLA KONTAKTUPPGIFTER:
   - Få alltid namn
   - Bekräfta telefon: "Vill du bli kontaktad på ett annat nummer än detta?"
   - Fråga efter e-post vid behov: "Vilken e-post vill du använda?"
   - Upprepa detaljer: "Jag uppfattade: [namn], [telefon], [mejl]. Stämmer det?"
4. ESKALERING/NÄSTA STEG:
   - Enkel fråga som du kan svara på → svara direkt
   - Kräver djupare rådgivning → föreslå möte
   - Annars → försäkra: "Jag ser till att en kollega kontaktar dig så fort som möjligt"
5. AVSLUTNING:
   - Sammanfatta kort: "[ärendet], [kontaktinfo]"
   - Avsluta artigt: "Tack, en medarbetare återkommer så fort de kan"

SKYDDSRÄCKEN:
- Ge aldrig priser, juridiska villkor eller löften
- Upprepa aldrig samma sak i olika meningar
- Hantera avbrott smidigt: stoppa, erkänn, fortsätt naturligt
- Om ljud otydligt: fråga en gång om upprepning, fortsätt sedan med det som förstås
- Tystnad >8s: be om nummer och avsluta
- Om utanför räckvidd: "Jag kan inte svara på det just nu, men jag vidarebefordrar ärendet"

Svara ALLTID på svenska och följ "en fråga i taget" principen."""

        super().__init__(instructions=system_prompt)
        self.session_ref = None
        self.ctx_ref = None

    def set_session_refs(self, session, ctx):
        """Store references for call ending"""
        self.session_ref = session
        self.ctx_ref = ctx


async def entrypoint(ctx: JobContext):
    """Main entrypoint for Robert's conversational agent - simplified working version"""
    await ctx.connect()

    # Initialize conversation tracking
    tracker = ConversationTracker()
    tracker.call_id = ctx.room.name

    logger.info(f"Starting Robert's call for room: {tracker.call_id}")

    # Create AgentSession with GPT-Realtime and Swedish configuration
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            model="gpt-realtime",  # 2025 GPT-Realtime model
            voice="cedar",  # Professional warm voice
            modalities=["audio", "text"],
            temperature=0.7,
            input_audio_transcription=InputAudioTranscription(
                model="whisper-1",
                language="sv",  # Swedish language
                prompt="Naturlig svensk konversation med professionell telefonassistent Robert"
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

    # Create Robert agent
    agent = RobertAgent()
    agent.set_session_refs(session, ctx)

    # Start the session with the agent
    await session.start(
        room=ctx.room,
        agent=agent
    )

    # Send automatic Swedish greeting following Robert's conversation rules
    greeting = "Hej, tack för att du ringde. Jag är företagets assistent. Hur kan jag hjälpa dig idag?"
    await session.generate_reply(
        instructions=f"Säg hälsningen på svenska: '{greeting}' och vänta på svar."
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))