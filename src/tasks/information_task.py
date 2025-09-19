"""
Information Collection Tasks - Structured data gathering
Demonstrates task-based workflow for collecting specific information
"""

import logging
from dataclasses import dataclass
from typing import Optional
from livekit.agents import AgentTask, function_tool

logger = logging.getLogger("information-task")


@dataclass
class ContactInformation:
    """Data class for collected contact information"""
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    preferred_contact: str = "phone"


@dataclass
class CallPurposeInfo:
    """Data class for call purpose information"""
    purpose: Optional[str] = None
    urgency: str = "normal"
    category: Optional[str] = None
    details: Optional[str] = None


class ContactInfoCollectionTask(AgentTask[ContactInformation]):
    """
    Task for collecting comprehensive contact information
    Returns ContactInformation dataclass with collected data
    """

    def __init__(self, required_fields: list = None, chat_ctx=None, language: str = "English"):
        self.language = language.lower()
        self.required_fields = required_fields or ["name", "phone"]
        self.collected_info = ContactInformation()

        if self.language in ["svenska", "swedish"]:
            instructions = f"""
Du ska samla in kontaktinformation från personen som ringer.
Obligatoriska fält: {', '.join(self.required_fields)}
Var vänlig och tydlig. Ställ en fråga i taget.
Bekräfta informationen när den är insamlad.
"""
        else:
            instructions = f"""
You need to collect contact information from the caller.
Required fields: {', '.join(self.required_fields)}
Be friendly and clear. Ask one question at a time.
Confirm information once collected.
"""

        super().__init__(
            instructions=instructions,
            chat_ctx=chat_ctx,
        )

    async def on_enter(self) -> None:
        """Start the information collection process"""
        if self.language in ["svenska", "swedish"]:
            start_message = "För att kunna hjälpa dig bäst, behöver jag samla in lite kontaktinformation. Vad heter du?"
        else:
            start_message = "To help you best, I need to collect some contact information. What's your name?"

        await self.session.generate_reply(instructions=f"Say: {start_message}")

    @function_tool
    async def record_name(self, name: str) -> None:
        """Record the caller's name"""
        self.collected_info.name = name
        logger.info(f"Name recorded: {name}")

        await self._continue_collection()

    @function_tool
    async def record_phone(self, phone: str) -> None:
        """Record the caller's phone number"""
        self.collected_info.phone = phone
        logger.info(f"Phone recorded: {phone}")

        await self._continue_collection()

    @function_tool
    async def record_email(self, email: str) -> None:
        """Record the caller's email address"""
        self.collected_info.email = email
        logger.info(f"Email recorded: {email}")

        await self._continue_collection()

    @function_tool
    async def record_company(self, company: str) -> None:
        """Record the caller's company"""
        self.collected_info.company = company
        logger.info(f"Company recorded: {company}")

        await self._continue_collection()

    @function_tool
    async def set_preferred_contact(self, method: str) -> None:
        """Set preferred contact method"""
        self.collected_info.preferred_contact = method.lower()
        logger.info(f"Preferred contact method: {method}")

        await self._continue_collection()

    async def _continue_collection(self):
        """Continue collecting required information or complete task"""
        missing_fields = []

        for field in self.required_fields:
            if field == "name" and not self.collected_info.name:
                missing_fields.append("name")
            elif field == "phone" and not self.collected_info.phone:
                missing_fields.append("phone")
            elif field == "email" and not self.collected_info.email:
                missing_fields.append("email")
            elif field == "company" and not self.collected_info.company:
                missing_fields.append("company")

        if not missing_fields:
            # All required information collected
            await self._confirm_and_complete()
        else:
            # Ask for next missing field
            await self._ask_for_field(missing_fields[0])

    async def _ask_for_field(self, field: str):
        """Ask for a specific field"""
        if self.language in ["svenska", "swedish"]:
            questions = {
                "name": "Vad heter du?",
                "phone": "Vad har du för telefonnummer?",
                "email": "Vad är din e-postadress?",
                "company": "Vilket företag representerar du?"
            }
        else:
            questions = {
                "name": "What's your name?",
                "phone": "What's your phone number?",
                "email": "What's your email address?",
                "company": "What company do you represent?"
            }

        question = questions.get(field, f"Please provide your {field}")
        await self.session.generate_reply(instructions=f"Ask: {question}")

    async def _confirm_and_complete(self):
        """Confirm collected information and complete task"""
        info_summary = []

        if self.collected_info.name:
            info_summary.append(f"Name: {self.collected_info.name}")
        if self.collected_info.phone:
            info_summary.append(f"Phone: {self.collected_info.phone}")
        if self.collected_info.email:
            info_summary.append(f"Email: {self.collected_info.email}")
        if self.collected_info.company:
            info_summary.append(f"Company: {self.collected_info.company}")

        summary = ", ".join(info_summary)

        if self.language in ["svenska", "swedish"]:
            confirmation = f"Tack! Jag har följande information: {summary}. Stämmer det?"
        else:
            confirmation = f"Thank you! I have the following information: {summary}. Is that correct?"

        await self.session.generate_reply(instructions=f"Say: {confirmation}")

    @function_tool
    async def confirm_information(self) -> None:
        """Confirm information is correct and complete task"""
        logger.info(f"Contact information confirmed: {self.collected_info}")

        if self.language in ["svenska", "swedish"]:
            completion_message = "Perfekt! Informationen är sparad."
        else:
            completion_message = "Perfect! The information has been saved."

        await self.session.generate_reply(instructions=f"Say: {completion_message}")
        self.complete(self.collected_info)

    @function_tool
    async def correct_information(self, field: str, new_value: str) -> None:
        """Correct specific information"""
        if field.lower() == "name":
            self.collected_info.name = new_value
        elif field.lower() == "phone":
            self.collected_info.phone = new_value
        elif field.lower() == "email":
            self.collected_info.email = new_value
        elif field.lower() == "company":
            self.collected_info.company = new_value

        logger.info(f"Information corrected - {field}: {new_value}")

        if self.language in ["svenska", "swedish"]:
            correction_message = f"Tack, jag har uppdaterat {field} till {new_value}."
        else:
            correction_message = f"Thank you, I've updated {field} to {new_value}."

        await self.session.generate_reply(instructions=f"Say: {correction_message}")
        await self._confirm_and_complete()


class CallPurposeTask(AgentTask[CallPurposeInfo]):
    """
    Task for understanding the purpose of the call
    Returns CallPurposeInfo with categorized information
    """

    def __init__(self, chat_ctx=None, language: str = "English"):
        self.language = language.lower()
        self.purpose_info = CallPurposeInfo()

        if self.language in ["svenska", "swedish"]:
            instructions = """
Du ska förstå anledningen till samtalet och kategorisera den.
Ställ öppna frågor för att förstå syftet.
Bedöm urgensen och kategorisera ärendet.
"""
        else:
            instructions = """
You need to understand the reason for the call and categorize it.
Ask open questions to understand the purpose.
Assess urgency and categorize the matter.
"""

        super().__init__(
            instructions=instructions,
            chat_ctx=chat_ctx,
        )

    async def on_enter(self) -> None:
        """Start understanding call purpose"""
        if self.language in ["svenska", "swedish"]:
            purpose_question = "Vad kan jag hjälpa dig med idag?"
        else:
            purpose_question = "What can I help you with today?"

        await self.session.generate_reply(instructions=f"Ask: {purpose_question}")

    @function_tool
    async def record_call_purpose(self, purpose: str, urgency: str = "normal", category: str = None) -> None:
        """Record the main purpose of the call"""
        self.purpose_info.purpose = purpose
        self.purpose_info.urgency = urgency.lower()
        self.purpose_info.category = category

        logger.info(f"Call purpose recorded: {purpose}, Urgency: {urgency}, Category: {category}")

        if urgency.lower() == "high":
            if self.language in ["svenska", "swedish"]:
                urgency_response = "Jag förstår att detta är brådskande. Låt mig prioritera ditt ärende."
            else:
                urgency_response = "I understand this is urgent. Let me prioritize your request."

            await self.session.generate_reply(instructions=f"Say: {urgency_response}")

        await self._ask_for_details()

    async def _ask_for_details(self):
        """Ask for additional details about the purpose"""
        if self.language in ["svenska", "swedish"]:
            details_question = "Kan du berätta lite mer om vad som har hänt eller vad du behöver hjälp med?"
        else:
            details_question = "Can you tell me a bit more about what happened or what you need help with?"

        await self.session.generate_reply(instructions=f"Ask: {details_question}")

    @function_tool
    async def add_details(self, details: str) -> None:
        """Add additional details about the call purpose"""
        self.purpose_info.details = details
        logger.info(f"Call details added: {details}")

        if self.language in ["svenska", "swedish"]:
            summary = f"Tack för informationen. Jag förstår att du behöver hjälp med: {self.purpose_info.purpose}."
        else:
            summary = f"Thank you for the information. I understand you need help with: {self.purpose_info.purpose}."

        await self.session.generate_reply(instructions=f"Say: {summary}")
        self.complete(self.purpose_info)

    @function_tool
    async def categorize_as_technical(self) -> None:
        """Categorize the call as technical support"""
        self.purpose_info.category = "technical"
        await self._complete_categorization()

    @function_tool
    async def categorize_as_billing(self) -> None:
        """Categorize the call as billing inquiry"""
        self.purpose_info.category = "billing"
        await self._complete_categorization()

    @function_tool
    async def categorize_as_sales(self) -> None:
        """Categorize the call as sales inquiry"""
        self.purpose_info.category = "sales"
        await self._complete_categorization()

    @function_tool
    async def categorize_as_general(self) -> None:
        """Categorize the call as general inquiry"""
        self.purpose_info.category = "general"
        await self._complete_categorization()

    async def _complete_categorization(self):
        """Complete the task with categorization"""
        logger.info(f"Call categorized as: {self.purpose_info.category}")

        if self.language in ["svenska", "swedish"]:
            category_message = f"Jag har kategoriserat ditt ärende som {self.purpose_info.category}."
        else:
            category_message = f"I've categorized your request as {self.purpose_info.category}."

        await self.session.generate_reply(instructions=f"Say: {category_message}")
        self.complete(self.purpose_info)