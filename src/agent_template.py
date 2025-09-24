"""
LiveKit Voice Agent Template
A fully configurable voice agent system with modular features
"""

import asyncio
import logging
import os
import time
import aiohttp
from datetime import datetime
from typing import Dict, Any, Optional
from livekit import agents, api, rtc
from livekit.agents import JobContext, WorkerOptions, cli, get_job_context
from livekit.agents.voice import AgentSession, Agent
from livekit.agents import ConversationItemAddedEvent, UserInputTranscribedEvent, function_tool
from livekit.plugins import openai
from dotenv import load_dotenv
import yaml

# Load environment variables
load_dotenv(".env.local")
load_dotenv()

logger = logging.getLogger("agent-template")


def load_config(config_path: str = None):
    """Load agent configuration from YAML file"""
    if not config_path:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "agent.config.yaml")

    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
            logger.info(f"Loaded agent configuration from {config_path}")
            return config or {}
    except Exception as e:
        logger.warning(f"Could not load agent config from {config_path}: {e}")
        return {}


class ConversationTracker:
    """Track conversation data for analytics and webhooks"""
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
    """Configurable memory system for tracking call information"""
    def __init__(self, config: Dict[str, Any]):
        self.config = config.get("memory", {})
        self.enabled = self.config.get("enabled", False)

        # Initialize tracked fields from config
        self.data = {}
        if self.enabled:
            for field in self.config.get("tracked_fields", []):
                if isinstance(field, str):
                    self.data[field] = None

    def update(self, field: str, value: Any):
        """Update a tracked field"""
        if self.enabled and field in self.data:
            self.data[field] = value
            logger.info(f"Memory updated: {field} = {value}")

    def get_summary(self):
        """Get current collected info as string"""
        if not self.enabled:
            return "Memory system disabled"

        info = []
        for field, value in self.data.items():
            if value:
                info.append(f"{field.title()}: {value}")

        return " | ".join(info) if info else "No information collected yet"


class SafetyMonitor:
    """Configurable safety monitoring system"""
    def __init__(self, config: Dict[str, Any]):
        self.config = config.get("safety", {})
        self.enabled = self.config.get("enabled", False)

        if self.enabled:
            self.max_duration = self.config.get("max_call_duration", 600)
            self.inactivity_timeout = self.config.get("inactivity_timeout", 30)
            self.disconnect_detection = self.config.get("participant_disconnect_detection", True)

            self.call_start_time = time.time()
            self.last_activity_time = time.time()
            self.monitor_task = None

    def update_activity(self):
        """Update last activity timestamp"""
        if self.enabled:
            self.last_activity_time = time.time()

    async def start_monitoring(self, session, ctx):
        """Start background safety monitoring"""
        if not self.enabled:
            return

        async def monitor():
            while True:
                try:
                    current_time = time.time()

                    # Check maximum call duration
                    if current_time - self.call_start_time > self.max_duration:
                        logger.warning(f"Call exceeded maximum duration ({self.max_duration}s)")
                        await self.end_call_gracefully(session, ctx)
                        break

                    # Check inactivity timeout
                    if current_time - self.last_activity_time > self.inactivity_timeout:
                        logger.warning(f"Call inactive for {self.inactivity_timeout}s")
                        await self.end_call_gracefully(session, ctx)
                        break

                    await asyncio.sleep(5)

                except Exception as e:
                    logger.error(f"Safety monitor error: {e}")
                    break

        self.monitor_task = asyncio.create_task(monitor())
        logger.info("Safety monitor started")

    async def end_call_gracefully(self, session, ctx):
        """End call with proper cleanup"""
        try:
            if self.monitor_task:
                self.monitor_task.cancel()

            if session:
                farewell = await session.generate_reply(
                    instructions="Say goodbye politely and end the call."
                )
                await asyncio.wait_for(farewell.wait(), timeout=10.0)
                await asyncio.sleep(1.0)

            if ctx:
                await ctx.api.room.delete_room(
                    api.DeleteRoomRequest(room=ctx.room.name)
                )
                logger.info("Call terminated by safety system")

        except Exception as e:
            logger.error(f"Error during safety termination: {e}")


class TemplateAgent(Agent):
    """Configurable template agent with modular features"""
    def __init__(self, config: Dict[str, Any], tools=None):
        self.config = config

        # Initialize features based on configuration
        self.memory = CallMemory(config) if config.get("memory", {}).get("enabled") else None
        self.safety = SafetyMonitor(config) if config.get("safety", {}).get("enabled") else None

        # Load prompt based on configuration
        prompt = self.load_prompt(config)

        # Initialize parent Agent class
        super().__init__(instructions=prompt, tools=tools or [])

        self.session_ref = None
        self.ctx_ref = None

    def load_prompt(self, config: Dict[str, Any]) -> str:
        """Load and configure prompt based on template or custom settings"""
        prompt_config = config.get("prompt", {})
        template = prompt_config.get("template", "conversational")

        if template == "custom":
            return prompt_config.get("custom_prompt", "You are a helpful assistant.")

        # Load from template library
        base_prompt = self.get_prompt_template(template, config)

        # Add business context
        business = config.get("business", {})
        if business.get("type"):
            base_prompt += f"\nBusiness Type: {business['type']}"

        # Add behavioral rules
        rules = prompt_config.get("rules", {})
        if rules.get("ask_one_question"):
            base_prompt += "\n- Always ask one question at a time"
        if rules.get("confirm_information"):
            base_prompt += "\n- Always confirm information by repeating it back"

        return base_prompt

    def get_prompt_template(self, template: str, config: Dict[str, Any]) -> str:
        """Get prompt template based on style and use case"""
        language = config.get("agent", {}).get("language", "English")
        use_case = config.get("prompt", {}).get("use_case", "general")

        templates = {
            "conversational": f"""You are a {config.get('agent', {}).get('personality_traits', 'friendly')} assistant.
                Speak {language} and maintain a natural conversation flow.
                Your purpose is to help with {use_case}.""",

            "formal": f"""You are a professional representative.
                Maintain formal communication in {language}.
                Handle {use_case} with strict professionalism.""",

            "technical": f"""You are a technical support specialist.
                Provide detailed technical assistance in {language}.
                Focus on resolving {use_case} efficiently."""
        }

        return templates.get(template, templates["conversational"])

    def set_session_refs(self, session, ctx):
        """Store session references for feature modules"""
        self.session_ref = session
        self.ctx_ref = ctx

        if self.safety:
            asyncio.create_task(self.safety.start_monitoring(session, ctx))

    # Dynamic function tools based on configuration
    @function_tool
    async def save_information(self, **kwargs):
        """Save information to memory (configurable fields)"""
        if not self.memory or not self.memory.enabled:
            return "Memory system is not enabled"

        for field, value in kwargs.items():
            if value:
                self.memory.update(field, value)

                # Update safety activity on user interaction
                if self.safety:
                    self.safety.update_activity()

        return f"Information saved: {self.memory.get_summary()}"

    @function_tool
    async def get_collected_information(self):
        """Get all collected information"""
        if not self.memory or not self.memory.enabled:
            return "Memory system is not enabled"

        return self.memory.get_summary()


async def send_webhook(config: Dict[str, Any], tracker: ConversationTracker):
    """Send conversation data to configured webhook"""
    webhook_config = config.get("integrations", {}).get("webhook", {})

    if not webhook_config.get("enabled"):
        return

    webhook_url = webhook_config.get("url") or os.getenv("WEBHOOK_URL")
    if not webhook_url:
        logger.info("No webhook URL configured")
        return

    payload = {
        "call_id": tracker.call_id,
        "conversation": tracker.conversation_data,
        "duration_seconds": tracker.get_duration(),
        "timestamp": int(time.time()),
        "config": {
            "agent_name": config.get("agent", {}).get("name"),
            "language": config.get("agent", {}).get("language")
        }
    }

    try:
        async with aiohttp.ClientSession() as session:
            headers = {}
            if webhook_config.get("auth_header"):
                headers["Authorization"] = webhook_config["auth_header"]

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
    """Main entrypoint for the template agent"""
    await ctx.connect()

    # Load configuration
    config = load_config()

    # Initialize conversation tracking
    tracker = ConversationTracker()
    tracker.call_id = ctx.room.name

    logger.info(f"Starting {config.get('agent', {}).get('name', 'Template')} agent for room: {tracker.call_id}")

    # Get configuration values
    agent_config = config.get("agent", {})
    voice_name = agent_config.get("voice", "cedar")
    language = agent_config.get("language", "English")
    model_config = config.get("model", {})

    logger.info(f"Using voice: {voice_name}, language: {language}")

    # Create AgentSession with configured model
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            model=model_config.get("name", "gpt-realtime"),
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

        # Update activity for safety monitoring
        if hasattr(session, '_agent_ref') and session._agent_ref and session._agent_ref.safety:
            session._agent_ref.safety.update_activity()

    @session.on("user_input_transcribed")
    def on_user_input_transcribed(event: UserInputTranscribedEvent):
        if event.is_final:
            logger.info(f"Final user transcript: {event.transcript}")
            # Update activity for safety monitoring
            if hasattr(session, '_agent_ref') and session._agent_ref and session._agent_ref.safety:
                session._agent_ref.safety.update_activity()

    # Participant disconnect detection
    if config.get("safety", {}).get("participant_disconnect_detection"):
        @ctx.room.on("participant_disconnected")
        def on_participant_disconnected(participant: rtc.RemoteParticipant):
            logger.info(f"Participant disconnected: {participant.identity}")
            if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_STANDARD:
                logger.warning("Caller disconnected, ending call")
                if agent.safety and agent.safety.monitor_task:
                    agent.safety.monitor_task.cancel()

    # Register webhook as shutdown callback
    if config.get("integrations", {}).get("webhook", {}).get("enabled"):
        async def send_completion_webhook():
            logger.info("Sending completion webhook...")
            await send_webhook(config, tracker)

        ctx.add_shutdown_callback(send_completion_webhook)

    # Extract caller phone number if configured
    caller_phone = None
    if config.get("memory", {}).get("auto_extract_phone"):
        for participant in ctx.room.remote_participants:
            if participant.identity.startswith("sip_"):
                caller_phone = participant.identity.replace("sip_", "")
                logger.info(f"Extracted caller phone: {caller_phone}")
                break

    # Create agent with configuration
    tools = []

    # Add end call tool if enabled
    if config.get("safety", {}).get("enabled"):
        @function_tool
        async def end_call():
            """End the call"""
            ctx = get_job_context()
            if ctx:
                await ctx.api.room.delete_room(
                    api.DeleteRoomRequest(room=ctx.room.name)
                )
                return "Call ended"
            return "Could not end call"

        tools.append(end_call)

    agent = TemplateAgent(config, tools=tools)
    agent.set_session_refs(session, ctx)

    # Store caller phone number if extracted and memory enabled
    if caller_phone and agent.memory:
        await agent.save_information(phone=caller_phone)
        logger.info(f"Auto-stored caller phone: {caller_phone}")

    # Store agent reference in session for event handlers
    session._agent_ref = agent

    # Start the session
    await session.start(
        room=ctx.room,
        agent=agent
    )

    # Send greeting message
    greeting = config.get("conversation", {}).get("first_message", "Hello, how can I help you today?")

    logger.info(f"Sending greeting: {greeting}")

    await asyncio.sleep(0.8)  # Small delay for audio pipeline
    greeting_handle = await session.generate_reply(
        instructions=f"Say the greeting: '{greeting}' and wait for response."
    )
    logger.info("Greeting sent successfully")


if __name__ == "__main__":
    # Only allow deployment entry point
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))