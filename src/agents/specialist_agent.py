"""
Specialist Agents - Domain-specific agents for technical, billing, etc.
These agents have specialized knowledge and tools for specific domains
"""

import logging
from typing import List, Optional
from livekit.agents import function_tool

from .base_agent import BaseAgent, AgentConfig

logger = logging.getLogger("specialist-agent")


class SpecialistAgent(BaseAgent):
    """
    Base class for specialist agents (Technical, Billing, etc.)
    Provides common specialist functionality
    """

    def __init__(self, config: AgentConfig, specialty: str, tools: List = None, chat_ctx=None):
        self.specialty = specialty

        # Add specialist-specific tools
        specialist_tools = [
            self.assess_issue_complexity,
            self.escalate_to_manager,
            self.provide_specialist_help,
        ]
        if tools:
            specialist_tools.extend(tools)

        super().__init__(config, specialist_tools, chat_ctx)

    def _build_instructions(self) -> str:
        """Build instructions for specialist agent"""
        base_personality = self.config.personality
        language = self.config.language

        if language.lower() in ["svenska", "swedish"]:
            instructions = f"""
Du är {self.config.name}, en specialist inom {self.specialty}.
Din personlighet: {base_personality}

EXPERTOMRÅDE: {self.specialty}

HUVUDUPPGIFTER:
1. Introducera dig som specialist
2. Förstå det specifika problemet/behovet
3. Använd din expertis för att hjälpa
4. Eskalera till chef vid behov
5. Dokumentera lösningen

RIKTLINJER:
- Var professionell och kunnig
- Ställ specifika tekniska frågor
- Förklara lösningar tydligt
- Bekräfta att problemet är löst
- Eskalera komplexa ärenden

Du har djup kunskap inom {self.specialty} och kan lösa de flesta relaterade problem.
"""
        else:
            instructions = f"""
You are {self.config.name}, a specialist in {self.specialty}.
Your personality: {base_personality}

AREA OF EXPERTISE: {self.specialty}

PRIMARY RESPONSIBILITIES:
1. Introduce yourself as a specialist
2. Understand the specific issue/need
3. Use your expertise to provide solutions
4. Escalate to management when necessary
5. Document the resolution

GUIDELINES:
- Be professional and knowledgeable
- Ask specific technical questions
- Explain solutions clearly
- Confirm issues are resolved
- Escalate complex matters appropriately

You have deep knowledge in {self.specialty} and can resolve most related issues.
"""

        return instructions

    async def on_enter(self) -> None:
        """Called when specialist agent becomes active"""
        if self.tracker_ref:
            self.tracker_ref.add_item(
                role="system",
                content=f"Specialist agent ({self.specialty}) activated",
                agent_name=self.agent_name
            )

        # Generate specialist introduction
        if self.config.language.lower() in ["svenska", "swedish"]:
            intro_instruction = (
                f"Introducera dig som specialist inom {self.specialty}. "
                "Fråga hur du kan hjälpa med deras specifika behov."
            )
        else:
            intro_instruction = (
                f"Introduce yourself as a {self.specialty} specialist. "
                "Ask how you can help with their specific needs."
            )

        await self.generate_contextual_reply(intro_instruction)

    @function_tool
    async def assess_issue_complexity(self, issue_description: str, complexity_level: str = "medium"):
        """Assess the complexity of the reported issue"""
        if self.tracker_ref:
            self.tracker_ref.add_item(
                role="system",
                content=f"Issue assessed: {issue_description}, Complexity: {complexity_level}",
                agent_name=self.agent_name
            )

        if complexity_level.lower() == "high":
            return "This appears to be a complex issue. Let me gather some additional information and may need to involve our senior specialists."
        elif complexity_level.lower() == "low":
            return "This looks like something I can help you with right away. Let me walk you through the solution."
        else:
            return "I understand the issue. Let me work through this with you step by step."

    @function_tool
    async def escalate_to_manager(self, reason: str):
        """Escalate to management when needed"""
        if self.tracker_ref:
            self.tracker_ref.add_handoff(
                from_agent=self.agent_name,
                to_agent="EscalationAgent",
                reason=f"Escalation from {self.specialty}: {reason}"
            )

        return f"I'm going to connect you with my manager who can better assist with this situation: {reason}"

    @function_tool
    async def provide_specialist_help(self, solution_type: str, details: str):
        """Provide specialized assistance"""
        if self.tracker_ref:
            self.tracker_ref.add_item(
                role="system",
                content=f"Solution provided: {solution_type} - {details}",
                agent_name=self.agent_name
            )

        return f"I've provided a {solution_type} solution for your issue. The details have been documented."


class TechnicalAgent(SpecialistAgent):
    """Technical Support Specialist Agent"""

    def __init__(self, config: AgentConfig, tools: List = None, chat_ctx=None):
        tech_tools = [
            self.diagnose_technical_issue,
            self.provide_troubleshooting_steps,
            self.schedule_technical_callback,
        ]
        if tools:
            tech_tools.extend(tools)

        super().__init__(config, "Technical Support", tech_tools, chat_ctx)

    @function_tool
    async def diagnose_technical_issue(self, symptoms: str, device_type: str = None):
        """Diagnose technical issues based on symptoms"""
        if self.tracker_ref:
            self.tracker_ref.add_item(
                role="system",
                content=f"Technical diagnosis: {symptoms} on {device_type or 'unknown device'}",
                agent_name=self.agent_name
            )

        return f"Based on the symptoms you've described ({symptoms}), I can help you troubleshoot this issue."

    @function_tool
    async def provide_troubleshooting_steps(self, steps: str):
        """Provide step-by-step troubleshooting"""
        return f"Here are the troubleshooting steps: {steps}. Let me know when you've completed each step."

    @function_tool
    async def schedule_technical_callback(self, callback_time: str, issue_summary: str):
        """Schedule a technical callback for complex issues"""
        if self.tracker_ref:
            self.tracker_ref.add_item(
                role="system",
                content=f"Technical callback scheduled: {callback_time} for {issue_summary}",
                agent_name=self.agent_name
            )

        return f"I've scheduled a technical callback for {callback_time} to continue working on: {issue_summary}"


class BillingAgent(SpecialistAgent):
    """Billing and Account Specialist Agent"""

    def __init__(self, config: AgentConfig, tools: List = None, chat_ctx=None):
        billing_tools = [
            self.review_account_status,
            self.process_billing_inquiry,
            self.handle_payment_issue,
        ]
        if tools:
            billing_tools.extend(tools)

        super().__init__(config, "Billing and Accounts", billing_tools, chat_ctx)

    @function_tool
    async def review_account_status(self, account_id: str = None):
        """Review customer account status"""
        if self.tracker_ref:
            self.tracker_ref.add_item(
                role="system",
                content=f"Account review requested: {account_id or 'caller account'}",
                agent_name=self.agent_name
            )

        return "I'm reviewing your account status. Let me check your recent billing information."

    @function_tool
    async def process_billing_inquiry(self, inquiry_type: str, details: str):
        """Process various billing inquiries"""
        if self.tracker_ref:
            self.tracker_ref.add_item(
                role="system",
                content=f"Billing inquiry: {inquiry_type} - {details}",
                agent_name=self.agent_name
            )

        return f"I'm processing your {inquiry_type} inquiry. Here's what I can do to help: {details}"

    @function_tool
    async def handle_payment_issue(self, issue_type: str, amount: str = None):
        """Handle payment-related issues"""
        return f"I understand you have a {issue_type} issue. Let me help resolve this payment matter."


class SalesAgent(SpecialistAgent):
    """Sales Specialist Agent"""

    def __init__(self, config: AgentConfig, tools: List = None, chat_ctx=None):
        sales_tools = [
            self.assess_customer_needs,
            self.present_solution,
            self.schedule_sales_followup,
        ]
        if tools:
            sales_tools.extend(tools)

        super().__init__(config, "Sales", sales_tools, chat_ctx)

    @function_tool
    async def assess_customer_needs(self, needs_description: str):
        """Assess customer needs and requirements"""
        if self.tracker_ref:
            self.tracker_ref.add_item(
                role="system",
                content=f"Customer needs assessment: {needs_description}",
                agent_name=self.agent_name
            )

        return f"Based on your needs ({needs_description}), let me explore the best solutions for you."

    @function_tool
    async def present_solution(self, solution_name: str, benefits: str):
        """Present appropriate solutions to customers"""
        return f"I'd like to present {solution_name} which offers these benefits: {benefits}"

    @function_tool
    async def schedule_sales_followup(self, followup_time: str, next_steps: str):
        """Schedule sales follow-up meetings"""
        if self.tracker_ref:
            self.tracker_ref.add_item(
                role="system",
                content=f"Sales followup scheduled: {followup_time} - {next_steps}",
                agent_name=self.agent_name
            )

        return f"I've scheduled a follow-up for {followup_time} to discuss: {next_steps}"