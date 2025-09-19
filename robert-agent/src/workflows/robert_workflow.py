"""
Robert's Conversational Workflow - Orchestrates the complete call handling flow
Implements the hybrid approach with natural conversation and structured data collection
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional

from livekit import agents, api, rtc
from livekit.agents import JobContext, WorkerOptions, cli, get_job_context
from livekit.agents.voice import AgentSession

# Import our components
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from agents.base_agent import ConversationTracker, SessionUserData, ConfigLoader
from ..agents.receptionist_agent import ReceptionistAgent
from ..agents.specialist_agents import InsuranceSpecialist, SolarSpecialist
from ..tasks.call_categorization_task import CallCategorizationTask

# Import template system components
from tasks.information_task import ContactInfoCollectionTask

logger = logging.getLogger("robert-workflow")


class RobertConversationalWorkflow:
    """
    Main workflow orchestrator for Robert's conversational agent
    Implements natural call flow with intelligent routing
    """

    def __init__(self, config_path: str = None):
        # Load configuration
        if not config_path:
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'robert-agent-config.md')

        self.config = ConfigLoader.load_config(config_path)
        self.session: Optional[AgentSession] = None
        self.context: Optional[JobContext] = None
        self.tracker = ConversationTracker()
        self.current_agent: Optional = None

        # Conversation state
        self.call_categorized = False
        self.contact_collected = False
        self.consultation_offered = False

    async def initialize_session(self, ctx: JobContext) -> AgentSession:
        """Initialize the agent session with Swedish configuration"""
        await ctx.connect()
        self.context = ctx
        self.tracker.call_id = ctx.room.name

        logger.info(f"Starting Robert's conversational workflow for room: {self.tracker.call_id}")

        # Create AgentSession with Swedish configuration
        from livekit.plugins import openai
        from openai.types.beta.realtime.session import InputAudioTranscription

        self.session = AgentSession(
            llm=openai.realtime.RealtimeModel(
                model="gpt-realtime",
                voice="cedar",  # Warm, professional voice
                modalities=["audio", "text"],
                temperature=0.7,
                input_audio_transcription=InputAudioTranscription(
                    model="whisper-1",
                    language="sv",  # Swedish
                    prompt="Naturlig svensk konversation med professionell telefonassistent"
                )
            ),
            userdata=SessionUserData()
        )

        # Set up event handlers
        self._setup_event_handlers()

        return self.session

    def _setup_event_handlers(self):
        """Set up session event handlers for intelligent conversation tracking"""

        @self.session.on("conversation_item_added")
        def on_conversation_item_added(event):
            agent_name = self.current_agent.__class__.__name__ if self.current_agent else "system"
            self.tracker.add_item(
                role=event.item.role,
                content=event.item.text_content,
                agent_name=agent_name,
                timestamp=event.created_at
            )

            # Smart workflow progression based on conversation content
            if event.item.role == "user":
                asyncio.create_task(self._analyze_user_input(event.item.text_content))

        @self.session.on("user_input_transcribed")
        def on_user_input_transcribed(event):
            if event.is_final:
                logger.info(f"User said: {event.transcript}")

    async def _analyze_user_input(self, user_input: str):
        """Analyze user input to determine workflow progression"""
        if not self.current_agent:
            return

        # Check for conversation flow triggers
        user_lower = user_input.lower()

        # Detect completion signals
        completion_signals = ["tack", "bra", "det räcker", "inget mer", "nej tack"]
        if any(signal in user_lower for signal in completion_signals):
            # User might be ready to end
            if self.contact_collected and self.call_categorized:
                await self._initiate_closing()

        # Detect escalation needs
        escalation_signals = ["komplex", "svårt", "förstår inte", "kan inte hjälpa"]
        if any(signal in user_lower for signal in escalation_signals):
            await self._consider_escalation()

    async def run_conversational_workflow(self, ctx: JobContext):
        """Run the complete conversational workflow"""
        session = await self.initialize_session(ctx)

        try:
            # Phase 1: Receptionist greeting and initial intake
            await self._phase_1_greeting_and_intake()

            # Phase 2: Call categorization through conversation
            if not self.call_categorized:
                await self._phase_2_call_categorization()

            # Phase 3: Contact collection (natural integration)
            if not self.contact_collected:
                await self._phase_3_contact_collection()

            # Phase 4: Specialist consultation or simple resolution
            await self._phase_4_resolution_or_escalation()

            # Phase 5: Polite closing with summary
            await self._phase_5_closing()

        except Exception as e:
            logger.error(f"Workflow error: {e}")
            await self._handle_workflow_error(e)

        finally:
            # Send completion data
            await self._send_completion_webhook()

    async def _phase_1_greeting_and_intake(self):
        """Phase 1: Professional greeting and initial intake"""
        logger.info("Phase 1: Greeting and initial intake")

        # Create and start receptionist agent
        from agents.base_agent import AgentConfig
        receptionist_config = AgentConfig(
            name="ReceptionistAssistant",
            voice="cedar",
            personality="calm, professional, conversational, human-like",
            specialization="call_intake_and_routing",
            language="Svenska"
        )

        self.current_agent = ReceptionistAgent(config=receptionist_config)
        self.current_agent.set_session_refs(self.session, self.context, self.tracker)

        # Start session with receptionist
        await self.session.start(room=self.context.room, agent=self.current_agent)

        # Natural greeting (handled by agent's on_enter)
        await self.current_agent.on_enter()

    async def _phase_2_call_categorization(self):
        """Phase 2: Understand call purpose through natural conversation"""
        logger.info("Phase 2: Call categorization")

        # Use categorization task for structured understanding
        categorization_task = CallCategorizationTask(
            chat_ctx=self.session.chat_ctx,
            language="Svenska"
        )

        # Run categorization as part of natural flow
        try:
            categorization_result = await categorization_task

            # Store results in session data
            if hasattr(self.session, 'userdata'):
                userdata = self.session.userdata
                userdata.call_purpose = categorization_result.category
                userdata.urgency_level = categorization_result.urgency

            self.call_categorized = True
            logger.info(f"Call categorized as: {categorization_result.category}")

            # Decide on specialist routing
            if categorization_result.requires_specialist:
                await self._route_to_specialist(categorization_result.category)

        except Exception as e:
            logger.error(f"Categorization failed: {e}")
            # Continue with general handling

    async def _phase_3_contact_collection(self):
        """Phase 3: Collect contact information naturally"""
        logger.info("Phase 3: Contact collection")

        # Use the current agent to collect contact info naturally
        if hasattr(self.current_agent, 'collect_contact_info'):
            # Natural contact collection through conversation
            await self.current_agent.collect_contact_info()
            self.contact_collected = True
        else:
            # Fallback to structured task
            contact_task = ContactInfoCollectionTask(
                required_fields=["name", "phone"],
                chat_ctx=self.session.chat_ctx,
                language="Svenska"
            )

            try:
                contact_info = await contact_task
                self.contact_collected = True
                logger.info(f"Contact collected: {contact_info.name}")
            except Exception as e:
                logger.error(f"Contact collection failed: {e}")

    async def _route_to_specialist(self, category: str):
        """Route to appropriate specialist agent"""
        logger.info(f"Routing to specialist for: {category}")

        from agents.base_agent import AgentConfig

        if category == "insurance":
            specialist_config = AgentConfig(
                name="InsuranceSpecialist",
                voice="cedar",
                personality="knowledgeable, patient, detail-oriented",
                specialization="insurance_inquiries",
                language="Svenska"
            )
            specialist = InsuranceSpecialist(config=specialist_config, chat_ctx=self.session.chat_ctx)

        elif category == "solar":
            specialist_config = AgentConfig(
                name="SolarSpecialist",
                voice="cedar",
                personality="enthusiastic, technical, solution-focused",
                specialization="solar_installation",
                language="Svenska"
            )
            specialist = SolarSpecialist(config=specialist_config, chat_ctx=self.session.chat_ctx)

        else:
            # Continue with receptionist for general inquiries
            return

        # Hand off to specialist
        specialist.set_session_refs(self.session, self.context, self.tracker)
        self.session.update_agent(specialist)
        self.current_agent = specialist

        # Specialist introduction
        await specialist.on_enter()

        # Track handoff
        self.tracker.add_handoff(
            from_agent="ReceptionistAgent",
            to_agent=specialist.__class__.__name__,
            reason=f"Specialist consultation for {category}"
        )

    async def _phase_4_resolution_or_escalation(self):
        """Phase 4: Provide resolution or escalate to human"""
        logger.info("Phase 4: Resolution or escalation")

        # Let current agent handle the specific needs
        if hasattr(self.current_agent, 'propose_meeting'):
            await self.current_agent.propose_meeting()
            self.consultation_offered = True

    async def _phase_5_closing(self):
        """Phase 5: Polite closing with summary"""
        logger.info("Phase 5: Closing conversation")

        if hasattr(self.current_agent, 'close_conversation'):
            await self.current_agent.close_conversation()
        else:
            # Fallback closing
            closing = "Tack för ditt samtal. En medarbetare återkommer så fort de kan."
            await self.session.generate_reply(instructions=f"Avsluta artigt: '{closing}'")

    async def _initiate_closing(self):
        """Initiate conversation closing when appropriate"""
        if hasattr(self.current_agent, 'close_conversation'):
            await self.current_agent.close_conversation()

    async def _consider_escalation(self):
        """Consider escalating to human based on complexity"""
        if hasattr(self.current_agent, 'escalate_to_human'):
            await self.current_agent.escalate_to_human(
                reason="complex",
                summary="Customer needs more specialized assistance"
            )

    async def _handle_workflow_error(self, error: Exception):
        """Handle workflow errors gracefully"""
        logger.error(f"Workflow error: {error}")

        error_response = "Ursäkta, jag hade ett tekniskt problem. Låt mig se till att du får hjälp på annat sätt."

        try:
            await self.session.generate_reply(instructions=f"Hantera fel: '{error_response}'")
        except:
            # Last resort - end call gracefully
            if self.current_agent:
                await self.current_agent.end_call_gracefully("Tack för ditt samtal.")

    async def _send_completion_webhook(self):
        """Send completion webhook with conversation summary"""
        webhook_url = self.config.get("integrations", {}).get("webhook", {}).get("url")
        if not webhook_url:
            return

        import aiohttp

        payload = self.tracker.get_summary()
        payload.update({
            "workflow_type": "conversational",
            "phases_completed": {
                "greeting": True,
                "categorization": self.call_categorized,
                "contact_collection": self.contact_collected,
                "consultation_offered": self.consultation_offered
            },
            "conversation_quality": "natural",  # Could be computed
            "language": "svenska"
        })

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload, timeout=30) as response:
                    if response.status == 200:
                        logger.info("Completion webhook sent successfully")
                    else:
                        logger.error(f"Webhook failed: {response.status}")
        except Exception as e:
            logger.error(f"Webhook error: {e}")


async def entrypoint(ctx: JobContext):
    """Main entrypoint for Robert's conversational agent"""
    workflow = RobertConversationalWorkflow()
    await workflow.run_conversational_workflow(ctx)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))