"""
Primary Agent - The main entry point agent for most conversations
Handles initial greeting, basic inquiries, and routing to specialists
"""

import logging
from typing import List, Optional
from livekit.agents import function_tool

from .base_agent import BaseAgent, AgentConfig

logger = logging.getLogger("primary-agent")


class PrimaryAgent(BaseAgent):
    """
    Primary agent that handles initial contact and general inquiries
    Routes to specialist agents when needed
    """

    def __init__(self, config: AgentConfig, tools: List = None, chat_ctx=None):
        # Add primary agent specific tools
        primary_tools = [
            self.collect_caller_info,
            self.categorize_call,
            self.provide_general_info,
        ]
        if tools:
            primary_tools.extend(tools)

        super().__init__(config, primary_tools, chat_ctx)

    def _build_instructions(self) -> str:
        """Build instructions specific to primary agent role"""
        # Check if we have a custom prompt from config
        if hasattr(self, 'custom_prompt') and self.custom_prompt:
            return self.custom_prompt

        # Fallback to default instructions
        base_personality = self.config.personality
        language = self.config.language

        if language.lower() in ["svenska", "swedish"]:
            instructions = f"""
Du är {self.config.name}, en hjälpsam röstassistent för {self.config.specialization}.
Din personlighet: {base_personality}

HUVUDUPPGIFTER:
1. Hälsa vänligt och identifiera vem som ringer
2. Ta reda på syftet med samtalet
3. Samla grundläggande kontaktinformation
4. Hjälp med enkla frågor eller dirigera till specialist
5. Håll samtalet naturligt och effektivt

RIKTLINJER:
- Ställ en fråga i taget
- Var tydlig och lyssna aktivt
- Bekräfta viktig information
- Erbjud hjälp proaktivt
- Avsluta vänligt när samtalet är klart

Svara ALLTID på svenska, även om användaren pratar annat språk.
"""
        else:
            instructions = f"""
You are {self.config.name}, a helpful voice assistant for {self.config.specialization}.
Your personality: {base_personality}

PRIMARY RESPONSIBILITIES:
1. Greet callers warmly and identify who's calling
2. Understand the purpose of their call
3. Collect basic contact information
4. Help with simple inquiries or route to specialists
5. Keep conversations natural and efficient

GUIDELINES:
- Ask one question at a time
- Be clear and listen actively
- Confirm important information
- Offer help proactively
- End calls politely when complete

Always maintain a {base_personality} tone throughout the conversation.
"""

        return instructions

    async def on_enter(self) -> None:
        """Called when primary agent becomes active"""
        if self.tracker_ref:
            self.tracker_ref.add_item(
                role="system",
                content=f"Primary agent ({self.config.name}) activated",
                agent_name=self.agent_name
            )

        # Generate greeting based on language
        if self.config.language.lower() in ["svenska", "swedish"]:
            greeting_instruction = (
                "Hälsa vänligt och fråga vem som ringer. "
                "Säg att du är här för att hjälpa till."
            )
        else:
            greeting_instruction = (
                "Greet the caller warmly and ask who you're speaking with. "
                "Let them know you're here to help."
            )

        await self.generate_contextual_reply(greeting_instruction)

    def should_handoff(self, user_input: str) -> tuple[bool, str, str]:
        """Determine if handoff to specialist is needed"""
        user_input_lower = user_input.lower()

        # Technical support keywords
        technical_keywords = [
            "technical", "tech", "not working", "broken", "error", "bug",
            "teknisk", "fungerar inte", "trasig", "fel", "problem"
        ]

        # Billing keywords
        billing_keywords = [
            "billing", "payment", "invoice", "charge", "refund", "bill",
            "faktura", "betalning", "återbetalning", "kostnad"
        ]

        # Escalation keywords
        escalation_keywords = [
            "manager", "supervisor", "escalate", "complaint", "angry",
            "chef", "klagomål", "arg", "missnöjd"
        ]

        if any(keyword in user_input_lower for keyword in technical_keywords):
            return True, "TechnicalAgent", "Technical support request"

        if any(keyword in user_input_lower for keyword in billing_keywords):
            return True, "BillingAgent", "Billing inquiry"

        if any(keyword in user_input_lower for keyword in escalation_keywords):
            return True, "EscalationAgent", "Escalation requested"

        return False, "", ""

    @function_tool
    async def collect_caller_info(self, name: str, phone: str = None, email: str = None):
        """Collect and store caller information"""
        if self.session_ref and hasattr(self.session_ref, 'userdata'):
            userdata = self.session_ref.userdata
            userdata.caller_name = name
            if phone:
                userdata.caller_phone = phone
            if email:
                userdata.caller_email = email

        if self.tracker_ref:
            self.tracker_ref.add_item(
                role="system",
                content=f"Caller info collected: {name}, {phone or 'no phone'}, {email or 'no email'}",
                agent_name=self.agent_name
            )

        return f"Thank you {name}, I have your information recorded."

    @function_tool
    async def categorize_call(self, purpose: str, urgency: str = "normal"):
        """Assess and categorize the call purpose"""
        if self.session_ref and hasattr(self.session_ref, 'userdata'):
            userdata = self.session_ref.userdata
            userdata.call_purpose = purpose
            userdata.urgency_level = urgency

        if self.tracker_ref:
            self.tracker_ref.add_item(
                role="system",
                content=f"Call purpose: {purpose}, Urgency: {urgency}",
                agent_name=self.agent_name
            )

        # Check if handoff is needed based on purpose
        should_handoff, target_agent, reason = self.should_handoff(purpose)
        if should_handoff:
            return f"I understand you need help with {purpose}. Let me connect you with our {target_agent.replace('Agent', '')} specialist."

        return f"I understand you're calling about {purpose}. How can I help you with this?"

    @function_tool
    async def provide_general_info(self, topic: str):
        """Provide general information on common topics"""
        if self.tracker_ref:
            self.tracker_ref.add_item(
                role="system",
                content=f"General info requested: {topic}",
                agent_name=self.agent_name
            )

        # This would integrate with a knowledge base in production
        return f"I can help with general questions about {topic}. What specifically would you like to know?"

    @function_tool
    async def transfer_to_specialist(self, specialist_type: str, reason: str):
        """Transfer to a specialist agent"""
        if self.tracker_ref:
            self.tracker_ref.add_handoff(
                from_agent=self.agent_name,
                to_agent=f"{specialist_type}Agent",
                reason=reason
            )

        return f"I'm transferring you to our {specialist_type} specialist who can better assist you. One moment please."