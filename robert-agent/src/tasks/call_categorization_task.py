"""
Call Categorization Task - Structured task for understanding call purpose
Implements natural conversation flow for categorizing caller intent
"""

import logging
from dataclasses import dataclass
from typing import Optional, List
from livekit.agents import AgentTask, function_tool

logger = logging.getLogger("call-categorization")


@dataclass
class CallPurposeResult:
    """Result from call categorization task"""
    category: str
    confidence: float
    details: str
    urgency: str = "normal"
    requires_specialist: bool = False
    suggested_follow_up: Optional[str] = None


class CallCategorizationTask(AgentTask[CallPurposeResult]):
    """
    Task for understanding and categorizing the caller's purpose
    Uses natural conversation to determine intent and route appropriately
    """

    def __init__(self, chat_ctx=None, language: str = "Svenska"):
        self.language = language.lower()
        self.categorization_result = CallPurposeResult(
            category="unknown",
            confidence=0.0,
            details=""
        )

        instructions = """
Du ska förstå anledningen till samtalet genom naturlig konversation.

MÅL:
- Kategorisera ärendet (försäkring, solceller, support, allmänt)
- Bedöma komplexitet och brådskande
- Bestämma om specialistrådgivning behövs

PRINCIPER:
- Ställ EN specifik fråga i taget
- Lyssna aktivt och ställ följdfrågor
- Använd naturliga övergångar
- Bekräfta förståelse med egna ord

Du ska INTE samla kontaktuppgifter här - fokusera bara på att förstå ärendet.
"""

        super().__init__(
            instructions=instructions,
            chat_ctx=chat_ctx,
        )

    async def on_enter(self) -> None:
        """Start call categorization"""
        # The receptionist agent has already greeted, so we listen for the purpose
        opening = "Låt mig förstå hur jag bäst kan hjälpa dig."
        await self.session.generate_reply(instructions=f"Säg: {opening}")

    @function_tool
    async def initial_categorization(self, user_statement: str, category_guess: str = None) -> None:
        """Make initial categorization of the call purpose"""

        # Category detection keywords
        category_patterns = {
            "insurance": ["försäkring", "premie", "avgift", "täckning", "skydd", "risk", "jämföra"],
            "solar": ["solcell", "anläggning", "installation", "panel", "energi", "el", "tak"],
            "support": ["problem", "fungerar inte", "fel", "trasig", "hjälp", "support", "teknisk"],
            "billing": ["faktura", "betalning", "kostnad", "pris", "räkning"],
            "general": ["information", "fråga", "vill veta", "undrar", "allmänt"]
        }

        user_lower = user_statement.lower()
        detected_category = category_guess or "general"
        confidence = 0.5

        # Smart pattern matching
        for category, keywords in category_patterns.items():
            matches = sum(1 for keyword in keywords if keyword in user_lower)
            if matches > 0:
                detected_category = category
                confidence = min(0.9, 0.5 + (matches * 0.2))
                break

        self.categorization_result.category = detected_category
        self.categorization_result.confidence = confidence
        self.categorization_result.details = user_statement

        logger.info(f"Initial categorization: {detected_category} (confidence: {confidence})")

        # Determine if specialist is needed
        specialist_categories = ["insurance", "solar", "support"]
        self.categorization_result.requires_specialist = detected_category in specialist_categories

        # Ask appropriate follow-up based on category
        await self._ask_category_specific_followup(detected_category)

    async def _ask_category_specific_followup(self, category: str):
        """Ask category-specific follow-up questions"""

        follow_up_questions = {
            "insurance": "Okej, gäller det din nuvarande försäkring eller är du intresserad av något nytt?",
            "solar": "Jag förstår. Gäller det en befintlig anläggning eller funderar du på installation?",
            "support": "Kan du berätta lite mer om vad som inte fungerar som det ska?",
            "billing": "Handlar det om en faktura du fått eller vill du veta mer om priserna?",
            "general": "Vad är det du främst vill få hjälp med?"
        }

        question = follow_up_questions.get(category, "Kan du utveckla det lite mer?")
        await self.session.generate_reply(instructions=f"Ställ följdfråga: '{question}'")

    @function_tool
    async def refine_categorization(self, additional_info: str, urgency_level: str = "normal") -> None:
        """Refine categorization based on additional information"""

        # Update details with additional context
        self.categorization_result.details += f" | {additional_info}"
        self.categorization_result.urgency = urgency_level

        # Assess urgency indicators
        urgent_keywords = ["brådskande", "akut", "snabbt", "direkt", "omedelbart", "problem"]
        if any(keyword in additional_info.lower() for keyword in urgent_keywords):
            self.categorization_result.urgency = "high"

        # Determine suggested follow-up
        if self.categorization_result.category == "insurance":
            if "jämföra" in additional_info.lower():
                self.categorization_result.suggested_follow_up = "comparison_consultation"
            else:
                self.categorization_result.suggested_follow_up = "policy_review"

        elif self.categorization_result.category == "solar":
            if "befintlig" in additional_info.lower() or "problem" in additional_info.lower():
                self.categorization_result.suggested_follow_up = "technical_support"
            else:
                self.categorization_result.suggested_follow_up = "installation_consultation"

        elif self.categorization_result.category == "support":
            self.categorization_result.suggested_follow_up = "technical_support"

        logger.info(f"Refined categorization: {self.categorization_result}")

        # Confirm understanding and complete
        await self._confirm_understanding()

    async def _confirm_understanding(self):
        """Confirm understanding of the caller's needs"""

        category_confirmations = {
            "insurance": "Jag förstår att det gäller försäkringsfrågor",
            "solar": "Okej, så det handlar om solceller",
            "support": "Jag förstår att det är ett tekniskt problem",
            "billing": "Det gäller alltså ekonomiska frågor",
            "general": "Jag förstår vad du behöver hjälp med"
        }

        confirmation = category_confirmations.get(
            self.categorization_result.category,
            "Jag förstår ditt ärende"
        )

        # Add urgency acknowledgment if high
        if self.categorization_result.urgency == "high":
            confirmation += " och att det är brådskande"

        await self.session.generate_reply(instructions=f"Bekräfta förståelse: '{confirmation}.'")

        # Complete the task
        self.complete(self.categorization_result)

    @function_tool
    async def request_clarification(self, unclear_aspect: str) -> None:
        """Request clarification when caller's intent is unclear"""

        clarification_questions = {
            "scope": "Kan du vara lite mer specifik om vad du vill ha hjälp med?",
            "urgency": "Är det något som behöver lösas snabbt?",
            "type": "Vilken typ av hjälp skulle vara mest användbar för dig?",
            "context": "Kan du berätta lite mer om bakgrunden?"
        }

        question = clarification_questions.get(unclear_aspect, "Kan du förklara lite mer?")

        logger.info(f"Requesting clarification about: {unclear_aspect}")
        await self.session.generate_reply(instructions=f"Be om förtydligande: '{question}'")

    @function_tool
    async def handle_multiple_issues(self, primary_issue: str, secondary_issue: str = None) -> None:
        """Handle cases where caller has multiple issues"""

        if secondary_issue:
            # Prioritize the issues
            response = f"Jag hör att du har frågor om både {primary_issue} och {secondary_issue}. Vad är viktigast att börja med?"
        else:
            # Focus on primary issue
            response = f"Låt oss fokusera på {primary_issue} först."

        await self.session.generate_reply(instructions=f"Prioritera: '{response}'")

    @function_tool
    async def detect_emotional_state(self, emotion: str, response_needed: bool = True) -> None:
        """Detect and respond to caller's emotional state"""

        if emotion == "frustrated":
            if response_needed:
                response = "Jag förstår att det här är frustrerande. Låt mig se till att du får rätt hjälp."
                await self.session.generate_reply(instructions=f"Visa empati: '{response}'")

        elif emotion == "confused":
            if response_needed:
                response = "Inga problem, låt mig hjälpa dig reda ut det här steg för steg."
                await self.session.generate_reply(instructions=f"Vara tålmodig: '{response}'")

        elif emotion == "urgent":
            self.categorization_result.urgency = "high"
            if response_needed:
                response = "Jag förstår att det här är brådskande. Jag ska se till att du får snabb hjälp."
                await self.session.generate_reply(instructions=f"Erkänn brådska: '{response}'")