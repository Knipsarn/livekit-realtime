"""
Main Workflow Orchestrator - Coordinates agent workflows and task execution
This is the central orchestration system for complex multi-agent workflows
"""

import asyncio
import logging
import os
import time
from typing import Dict, Any, Optional, Type, Union
from enum import Enum
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")
load_dotenv()

from livekit import agents, api, rtc
from livekit.agents import JobContext, WorkerOptions, cli, get_job_context
from livekit.agents.voice import AgentSession

from agents.base_agent import (
    BaseAgent, AgentConfig, SessionUserData, ConversationTracker,
    ConfigLoader, create_agent_config
)
from agents.primary_agent import PrimaryAgent
from agents.specialist_agent import TechnicalAgent, BillingAgent, SalesAgent
from tasks.consent_task import ConsentCollectionTask, DataCollectionConsentTask
from tasks.information_task import ContactInfoCollectionTask, CallPurposeTask

logger = logging.getLogger("workflow-orchestrator")


class WorkflowType(Enum):
    """Supported workflow types"""
    SINGLE_AGENT = "single_agent"
    MULTI_AGENT = "multi_agent"
    TASK_BASED = "task_based"
    HYBRID = "hybrid"


class WorkflowOrchestrator:
    """
    Main workflow orchestrator that manages agent transitions and task execution
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.workflow_type = WorkflowType(config.get("workflow_type", "single_agent"))
        self.session: Optional[AgentSession] = None
        self.context: Optional[JobContext] = None
        self.tracker = ConversationTracker()
        self.current_agent: Optional[BaseAgent] = None
        self.max_handoffs = config.get("workflow", {}).get("max_handoffs", 5)
        self.handoff_count = 0

        # Agent registry
        self.agent_classes = {
            "PrimaryAgent": PrimaryAgent,
            "TechnicalAgent": TechnicalAgent,
            "BillingAgent": BillingAgent,
            "SalesAgent": SalesAgent,
        }

    async def initialize_session(self, ctx: JobContext) -> AgentSession:
        """Initialize the agent session with proper configuration"""
        await ctx.connect()
        self.context = ctx
        self.tracker.call_id = ctx.room.name

        logger.info(f"Starting workflow: {self.workflow_type.value} for room: {self.tracker.call_id}")

        # Create session configuration
        voice_name = self.config.get("voice", "cedar")
        language = self.config.get("language", "English")
        model_config = self.config.get("advanced", {}).get("model_overrides", {})

        # Create AgentSession
        from livekit.plugins import openai
        from openai.types.beta.realtime.session import InputAudioTranscription

        self.session = AgentSession(
            llm=openai.realtime.RealtimeModel(
                model=model_config.get("primary_model", "gpt-realtime"),
                voice=voice_name,
                modalities=["audio", "text"],
                temperature=model_config.get("temperature", 0.7),
                # Add transcription if configured
                input_audio_transcription=InputAudioTranscription(
                    model="whisper-1",
                    language="sv" if language.lower() in ["svenska", "swedish"] else "en",
                    prompt="Naturlig svensk konversation med professionell telefonassistent Robert" if language.lower() in ["svenska", "swedish"] else "Natural conversation with professional phone assistant"
                ) if self.config.get("integrations", {}).get("telephony", {}).get("transcription", True) else None
            ),
            userdata=SessionUserData()
        )

        # Set up event handlers
        self._setup_event_handlers()

        return self.session

    def _setup_event_handlers(self):
        """Set up session event handlers for tracking"""
        @self.session.on("conversation_item_added")
        def on_conversation_item_added(event):
            agent_name = self.current_agent.agent_name if self.current_agent else "unknown"
            self.tracker.add_item(
                role=event.item.role,
                content=event.item.text_content,
                agent_name=agent_name,
                timestamp=event.created_at
            )
            logger.info(f"Conversation item from {event.item.role}: {event.item.text_content[:50]}...")

        @self.session.on("user_input_transcribed")
        def on_user_input_transcribed(event):
            if event.is_final and self.current_agent:
                logger.info(f"User transcript: {event.transcript}")
                # Check if handoff is needed
                asyncio.create_task(self._check_handoff_triggers(event.transcript))

    async def _check_handoff_triggers(self, user_input: str):
        """Check if agent handoff is triggered by user input"""
        if not self.current_agent or self.handoff_count >= self.max_handoffs:
            return

        should_handoff, target_agent, reason = self.current_agent.should_handoff(user_input)
        if should_handoff and target_agent in self.agent_classes:
            await self._handoff_to_agent(target_agent, reason)

    async def _handoff_to_agent(self, target_agent_name: str, reason: str):
        """Perform agent handoff"""
        if self.handoff_count >= self.max_handoffs:
            logger.warning(f"Maximum handoffs ({self.max_handoffs}) reached")
            return

        target_agent_class = self.agent_classes.get(target_agent_name)
        if not target_agent_class:
            logger.error(f"Unknown agent class: {target_agent_name}")
            return

        logger.info(f"Handing off from {self.current_agent.agent_name} to {target_agent_name}: {reason}")

        # Create new agent configuration
        agent_type = "secondary" if target_agent_name != "PrimaryAgent" else "primary"
        new_config = create_agent_config(self.config, agent_type)

        # Preserve context if configured
        chat_ctx = None
        if self.config.get("workflow", {}).get("context_preservation", True):
            chat_ctx = self.session.chat_ctx

        # Create new agent
        new_agent = target_agent_class(config=new_config, chat_ctx=chat_ctx)

        # Set custom prompt if available in config (for primary agents)
        if target_agent_name == "PrimaryAgent" and "prompt" in self.config:
            new_agent.custom_prompt = self.config["prompt"]
        new_agent.set_session_refs(self.session, self.context, self.tracker)

        # Update session
        self.session.update_agent(new_agent)
        self.current_agent = new_agent
        self.handoff_count += 1

        # Agent enters
        await new_agent.on_enter()

    async def run_workflow(self, ctx: JobContext):
        """Run the complete workflow based on configuration"""
        session = await self.initialize_session(ctx)

        try:
            if self.workflow_type == WorkflowType.TASK_BASED:
                await self._run_task_based_workflow()
            elif self.workflow_type == WorkflowType.MULTI_AGENT:
                await self._run_multi_agent_workflow()
            elif self.workflow_type == WorkflowType.HYBRID:
                await self._run_hybrid_workflow()
            else:
                await self._run_single_agent_workflow()

        except Exception as e:
            logger.error(f"Workflow error: {e}")
            raise

        finally:
            # Send webhook data
            await self._send_completion_webhook()

    async def _run_single_agent_workflow(self):
        """Run simple single agent workflow"""
        # Create primary agent
        primary_config = create_agent_config(self.config, "primary")
        self.current_agent = PrimaryAgent(config=primary_config)

        # Set custom prompt if available in config
        if "prompt" in self.config:
            self.current_agent.custom_prompt = self.config["prompt"]

        self.current_agent.set_session_refs(self.session, self.context, self.tracker)

        # Start session
        await self.session.start(room=self.context.room, agent=self.current_agent)

        # Initial greeting
        await self._send_initial_greeting()

    async def _run_multi_agent_workflow(self):
        """Run multi-agent workflow with handoffs"""
        # Start with primary agent
        await self._run_single_agent_workflow()
        # Handoffs handled by event handlers

    async def _run_task_based_workflow(self):
        """Run task-based workflow with structured data collection"""
        # Create primary agent for task coordination
        primary_config = create_agent_config(self.config, "primary")
        self.current_agent = PrimaryAgent(config=primary_config)

        # Set custom prompt if available in config
        if "prompt" in self.config:
            self.current_agent.custom_prompt = self.config["prompt"]

        self.current_agent.set_session_refs(self.session, self.context, self.tracker)

        await self.session.start(room=self.context.room, agent=self.current_agent)

        # Run configured tasks in sequence
        if self.config.get("tasks", {}).get("consent_collection", {}).get("enabled", False):
            consent_result = await self._run_consent_task()
            if not consent_result and self.config.get("tasks", {}).get("consent_collection", {}).get("required", False):
                await self.current_agent.end_call_gracefully("Thank you for your time. Have a great day!")
                return

        if self.config.get("tasks", {}).get("information_gathering", {}).get("enabled", False):
            await self._run_information_gathering_task()

        # Continue with normal agent interaction
        await self._send_initial_greeting()

    async def _run_hybrid_workflow(self):
        """Run hybrid workflow combining tasks and multi-agent"""
        await self._run_task_based_workflow()
        # Multi-agent handoffs available after tasks

    async def _run_consent_task(self) -> bool:
        """Run consent collection task"""
        language = self.config.get("language", "English")
        consent_task = ConsentCollectionTask(
            chat_ctx=self.session.chat_ctx,
            language=language
        )
        return await consent_task

    async def _run_information_gathering_task(self):
        """Run information gathering task"""
        language = self.config.get("language", "English")
        required_fields = self.config.get("tasks", {}).get("information_gathering", {}).get("required_fields", "name,phone").split(",")

        contact_task = ContactInfoCollectionTask(
            required_fields=[field.strip() for field in required_fields],
            chat_ctx=self.session.chat_ctx,
            language=language
        )
        contact_info = await contact_task

        # Store in session userdata
        if hasattr(self.session, 'userdata'):
            userdata = self.session.userdata
            userdata.caller_name = contact_info.name
            userdata.caller_phone = contact_info.phone
            userdata.caller_email = contact_info.email

        return contact_info

    async def _send_initial_greeting(self):
        """Send initial greeting message"""
        greeting_message = self.config.get("first_message")
        if not greeting_message:
            language = self.config.get("language", "English")
            if language.lower() in ["svenska", "swedish"]:
                greeting_message = "Hej! Hur kan jag hjälpa dig idag?"
            else:
                greeting_message = "Hello! How can I help you today?"

        if self.config.get("use_prerecorded_greeting", False):
            # Try to play pre-recorded audio
            audio_played = await self._play_greeting_audio()
            if audio_played:
                return

        # Fallback to AI-generated greeting
        await self.current_agent.generate_contextual_reply(
            f"Say this greeting: '{greeting_message}'"
        )

    async def _play_greeting_audio(self) -> bool:
        """Play pre-recorded greeting audio"""
        try:
            audio_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "assets", "greetings", "greeting.wav"
            )

            if not os.path.exists(audio_path):
                logger.warning(f"Greeting audio not found: {audio_path}")
                return False

            # Audio playback implementation would go here
            # Similar to the samuel-dev implementation
            logger.info(f"Playing greeting audio: {audio_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to play greeting audio: {e}")
            return False

    async def _send_completion_webhook(self):
        """Send completion webhook with conversation data"""
        webhook_config = self.config.get("integrations", {}).get("webhook", {})
        if not webhook_config.get("enabled", False):
            return

        webhook_url = webhook_config.get("url")
        if not webhook_url:
            logger.warning("Webhook enabled but no URL configured")
            return

        import aiohttp

        payload = self.tracker.get_summary()
        payload.update({
            "workflow_type": self.workflow_type.value,
            "handoff_count": self.handoff_count,
            "config_summary": {
                "agents_used": list(set([item.get("agent") for item in self.tracker.conversation_data if item.get("agent")])),
                "language": self.config.get("language"),
                "voice": self.config.get("voice")
            }
        })

        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                auth_header = webhook_config.get("auth_header")
                if auth_header:
                    headers["Authorization"] = auth_header

                async with session.post(
                    webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        logger.info("Webhook sent successfully")
                    else:
                        logger.error(f"Webhook failed: {response.status}")

        except Exception as e:
            logger.error(f"Webhook error: {e}")


async def entrypoint(ctx: JobContext):
    """Main entrypoint for template-generated agents"""
    # Load configuration
    config = ConfigLoader.load_config()
    if not config:
        logger.error("Failed to load agent configuration")
        return

    # Create and run workflow
    orchestrator = WorkflowOrchestrator(config)
    await orchestrator.run_workflow(ctx)


# Entry point removed - only use lk agent deploy