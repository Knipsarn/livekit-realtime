"""
Base Agent Template - Foundation for all workflow agents
Provides common functionality and configuration loading
"""

import asyncio
import logging
import os
import time
import yaml
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from livekit import agents, api, rtc
from livekit.agents import JobContext, Agent, function_tool, get_job_context
from livekit.agents.voice import AgentSession
from livekit.agents import ConversationItemAddedEvent, UserInputTranscribedEvent
from livekit.plugins import openai
from openai.types.beta.realtime.session import InputAudioTranscription

logger = logging.getLogger("agent-template")


@dataclass
class AgentConfig:
    """Configuration data class for agent settings"""
    name: str
    voice: str
    personality: str
    specialization: str
    model: str = "gpt-realtime"
    temperature: float = 0.7
    language: str = "English"


@dataclass
class SessionUserData:
    """Custom session state data - extend as needed"""
    caller_name: Optional[str] = None
    caller_phone: Optional[str] = None
    caller_email: Optional[str] = None
    call_purpose: Optional[str] = None
    urgency_level: str = "normal"
    business_context: Optional[str] = None
    handoff_count: int = 0
    consent_given: Optional[bool] = None
    information_collected: bool = False


class ConfigLoader:
    """Loads and parses agent configuration with template variable substitution"""

    @staticmethod
    def load_config(config_path: str = None) -> Dict[str, Any]:
        """Load configuration from agent.creation.md"""
        if not config_path:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "config",
                "agent.creation.md"
            )

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

    @staticmethod
    def substitute_variables(config: Dict[str, Any], variables: Dict[str, str]) -> Dict[str, Any]:
        """Replace template variables with actual values"""
        def replace_in_value(value):
            if isinstance(value, str):
                for var, replacement in variables.items():
                    value = value.replace(f"{{{{{var}}}}}", str(replacement))
                return value
            elif isinstance(value, dict):
                return {k: replace_in_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [replace_in_value(item) for item in value]
            return value

        return replace_in_value(config)


class ConversationTracker:
    """Tracks conversation data for analytics and webhooks"""

    def __init__(self):
        self.conversation_data = []
        self.start_time = time.time()
        self.call_id = None
        self.agent_handoffs = []

    def add_item(self, role: str, content: str, agent_name: str = None, timestamp: float = None):
        """Add conversation item with agent tracking"""
        self.conversation_data.append({
            "role": role,
            "content": content,
            "agent": agent_name,
            "timestamp": timestamp or time.time(),
            "datetime": datetime.now().isoformat()
        })

    def add_handoff(self, from_agent: str, to_agent: str, reason: str = None):
        """Track agent handoffs"""
        self.agent_handoffs.append({
            "from_agent": from_agent,
            "to_agent": to_agent,
            "reason": reason,
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat()
        })

    def get_duration(self) -> float:
        """Get call duration in seconds"""
        return time.time() - self.start_time

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive call summary"""
        return {
            "call_id": self.call_id,
            "duration_seconds": self.get_duration(),
            "conversation": self.conversation_data,
            "handoffs": self.agent_handoffs,
            "start_time": self.start_time,
            "end_time": time.time()
        }


class BaseAgent(Agent, ABC):
    """
    Abstract base agent class providing common functionality for all agents
    Extend this class to create specific agent types
    """

    def __init__(self,
                 config: AgentConfig,
                 tools: List = None,
                 chat_ctx = None):

        self.config = config
        self.agent_name = config.name

        # Build instructions from config
        instructions = self._build_instructions()

        super().__init__(
            instructions=instructions,
            tools=tools or [],
            chat_ctx=chat_ctx
        )

        # Session references for coordination
        self.session_ref: Optional[AgentSession] = None
        self.ctx_ref: Optional[JobContext] = None
        self.tracker_ref: Optional[ConversationTracker] = None

    def set_session_refs(self, session: AgentSession, ctx: JobContext, tracker: ConversationTracker):
        """Set references to session components"""
        self.session_ref = session
        self.ctx_ref = ctx
        self.tracker_ref = tracker

    @abstractmethod
    def _build_instructions(self) -> str:
        """Build agent-specific instructions - must be implemented by subclasses"""
        pass

    @abstractmethod
    async def on_enter(self) -> None:
        """Called when agent becomes active - must be implemented by subclasses"""
        pass

    async def on_exit(self) -> None:
        """Called when agent is about to be replaced - override if needed"""
        pass

    def should_handoff(self, user_input: str) -> tuple[bool, str, str]:
        """
        Determine if handoff is needed based on user input
        Returns: (should_handoff, target_agent, reason)
        Override in subclasses for specific handoff logic
        """
        return False, "", ""

    async def generate_contextual_reply(self, instructions: str, context: Dict[str, Any] = None):
        """Generate reply with additional context"""
        if self.session_ref:
            full_instructions = instructions
            if context:
                context_str = " ".join([f"{k}: {v}" for k, v in context.items() if v])
                full_instructions = f"{instructions}\nContext: {context_str}"

            return await self.session_ref.generate_reply(instructions=full_instructions)

    async def transfer_to_agent(self, target_agent_class, reason: str = "User request"):
        """Handle agent transfer with proper tracking"""
        if self.tracker_ref:
            self.tracker_ref.add_handoff(
                from_agent=self.agent_name,
                to_agent=target_agent_class.__name__,
                reason=reason
            )

        await self.on_exit()
        return target_agent_class(config=self.config, chat_ctx=self.chat_ctx)

    async def end_call_gracefully(self, farewell_message: str = None):
        """End call with proper cleanup"""
        try:
            if self.session_ref and farewell_message:
                logger.info("Generating farewell message...")
                speech_handle = await self.session_ref.generate_reply(
                    instructions=f"Say this farewell message: '{farewell_message}'"
                )
                await asyncio.wait_for(speech_handle.wait(), timeout=10.0)
                await asyncio.sleep(1.0)

            # Delete room to end call
            if self.ctx_ref:
                logger.info(f"Ending call in room: {self.ctx_ref.room.name}")
                await self.ctx_ref.api.room.delete_room(
                    api.DeleteRoomRequest(room=self.ctx_ref.room.name)
                )
                logger.info("Call ended successfully")

        except Exception as e:
            logger.error(f"Error during call termination: {e}")
            # Ensure call still ends
            try:
                ctx = get_job_context()
                if ctx:
                    await ctx.api.room.delete_room(
                        api.DeleteRoomRequest(room=ctx.room.name)
                    )
            except Exception as cleanup_error:
                logger.error(f"Failed cleanup: {cleanup_error}")


# Base function tools that can be used by any agent
@function_tool
async def end_call_tool():
    """End the call when conversation is complete"""
    ctx = get_job_context()
    if ctx is None:
        return "Could not end call - no context available"

    logger.info("End call tool invoked")
    await ctx.api.room.delete_room(
        api.DeleteRoomRequest(room=ctx.room.name)
    )
    return "Call ended"


def create_agent_config(config_dict: Dict[str, Any], agent_type: str = "primary") -> AgentConfig:
    """Create AgentConfig from configuration dictionary"""
    agents_config = config_dict.get("agents", {})
    agent_config = agents_config.get(agent_type, {})

    return AgentConfig(
        name=agent_config.get("name", f"{agent_type}_agent"),
        voice=agent_config.get("voice", config_dict.get("voice", "cedar")),
        personality=agent_config.get("personality", config_dict.get("personality_traits", "friendly, professional")),
        specialization=agent_config.get("specialization", "general"),
        model=config_dict.get("advanced", {}).get("model_overrides", {}).get("primary_model", "gpt-realtime"),
        temperature=config_dict.get("advanced", {}).get("model_overrides", {}).get("temperature", 0.7),
        language=config_dict.get("language", "English")
    )