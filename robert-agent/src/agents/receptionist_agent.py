"""
Receptionist Agent - Main conversational agent for call intake and routing
Implements Robert's specification for natural, human-like call handling
"""

import logging
from typing import List, Optional, Dict, Any
from livekit.agents import function_tool
from dataclasses import dataclass

# Import base classes from template system
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from agents.base_agent import BaseAgent, AgentConfig

logger = logging.getLogger("receptionist-agent")


@dataclass
class CallCategory:
    """Call categorization data"""
    category: str
    confidence: float
    suggested_questions: List[str]
    requires_specialist: bool


@dataclass
class ContactDetails:
    """Contact information collection"""
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    confirmed: bool = False


class ReceptionistAgent(BaseAgent):
    """
    Main receptionist agent that handles call intake, categorization, and routing
    Implements Robert's conversational specifications
    """

    def __init__(self, config: AgentConfig, tools: List = None, chat_ctx=None):
        # Add receptionist-specific tools
        receptionist_tools = [
            self.categorize_call,
            self.collect_contact_info,
            self.propose_meeting,
            self.ask_clarifying_question,
            self.confirm_details,
            self.escalate_to_human,
        ]
        if tools:
            receptionist_tools.extend(tools)

        super().__init__(config, receptionist_tools, chat_ctx)

        # Conversation state
        self.call_category: Optional[CallCategory] = None
        self.contact_details = ContactDetails()
        self.questions_asked = []
        self.conversation_phase = "greeting"

    def _build_instructions(self) -> str:
        """Build instructions for the receptionist agent"""
        return """
Du är en professionell telefonassistent som svarar på vidarebefordrade samtal.

GRUNDPRINCIPER:
- Ställ EN fråga i taget - aldrig flera frågor samtidigt
- Korta, tydliga meningar (max ~15 ord per fråga)
- Lugn, professionell, samtalslik ton
- Använd fyllnadsord ibland ("okej," "hm," "jag förstår") för naturlighet
- Upprepa alltid namn, nummer och e-post för att bekräfta riktighet
- Ställ alltid följdfrågor på ett vägledande sätt, inte skriptad upprepning

SAMTALSFLÖDE:
1. HÄLSNING: "Hej, tack för att du ringde. Jag är företagets assistent. Hur kan jag hjälpa dig idag?"
2. IDENTIFIERA OCH KATEGORISERA: Lyssna och klassificera ärendet
3. SAMLA KONTAKTUPPGIFTER: Namn, telefon, e-post
4. ESKALERING/NÄSTA STEG: Föreslå möte eller försäkra om återkoppling
5. AVSLUTNING: Sammanfatta och avsluta artigt

SKYDDSRÄCKEN:
- Ge aldrig priser, juridiska villkor eller löften
- Hantera avbrott smidigt: stoppa, erkänn, fortsätt naturligt
- Om ljud otydligt: fråga en gång om upprepning
- Tystnad >8s: be om nummer och avsluta
- Om utanför räckvidd: "Jag kan inte svara på det just nu, men jag vidarebefordrar ärendet"

Du är varm, professionell och mänsklig. Få samtalet att flyta naturligt.
"""

    async def on_enter(self) -> None:
        """Called when receptionist agent becomes active"""
        if self.tracker_ref:
            self.tracker_ref.add_item(
                role="system",
                content="Receptionist agent activated - starting call intake",
                agent_name=self.agent_name
            )

        self.conversation_phase = "greeting"

        # Natural Swedish greeting
        greeting = "Hej, tack för att du ringde. Jag är företagets assistent. Hur kan jag hjälpa dig idag?"

        await self.generate_contextual_reply(f"Säg exakt: '{greeting}'")

    @function_tool
    async def categorize_call(self, purpose: str, category: str = None, confidence: float = 0.8) -> None:
        """Categorize the call purpose and determine next steps"""

        # Smart categorization logic
        category_mapping = {
            "insurance": ["försäkring", "avgift", "premie", "skydd", "täckning"],
            "solar": ["solcell", "anläggning", "installation", "panel", "energi"],
            "support": ["problem", "fungerar inte", "fel", "hjälp", "support"],
            "general": ["information", "fråga", "vill veta", "undrar"]
        }

        if not category:
            purpose_lower = purpose.lower()
            for cat, keywords in category_mapping.items():
                if any(keyword in purpose_lower for keyword in keywords):
                    category = cat
                    break
            else:
                category = "general"

        self.call_category = CallCategory(
            category=category,
            confidence=confidence,
            suggested_questions=self._get_category_questions(category),
            requires_specialist=(category in ["insurance", "solar"])
        )

        if self.tracker_ref:
            self.tracker_ref.add_item(
                role="system",
                content=f"Call categorized as: {category} (confidence: {confidence})",
                agent_name=self.agent_name
            )

        self.conversation_phase = "categorization_complete"

        # Provide natural response based on category
        if category == "insurance":
            response = "Okej, gäller det din nuvarande plan eller en ny?"
        elif category == "solar":
            response = "Gäller det en befintlig anläggning eller en ny installation?"
        elif category == "support":
            response = "Jag förstår. Kan du berätta lite mer om problemet?"
        else:
            response = "Jag förstår. Vad skulle du vilja veta?"

        await self.generate_contextual_reply(f"Svara naturligt: '{response}'")

    @function_tool
    async def ask_clarifying_question(self, context: str, question_type: str = "general") -> None:
        """Ask natural clarifying questions based on context"""

        if question_type in self.questions_asked:
            # Avoid repetition - ask different angle
            if question_type == "scope":
                question = "Vilken del av det här är viktigast för dig?"
            elif question_type == "timeline":
                question = "Är det något som behöver lösas snabbt?"
            else:
                question = "Kan du berätta lite mer?"
        else:
            # Fresh question types
            question_bank = {
                "scope": "Gäller det en befintlig situation eller något nytt?",
                "timeline": "Är det brådskande eller kan det vänta?",
                "specifics": "Vad är det viktigaste du vill få svar på?",
                "general": "Kan du berätta lite mer om det?"
            }
            question = question_bank.get(question_type, "Kan du utveckla det lite?")

        self.questions_asked.append(question_type)

        if self.tracker_ref:
            self.tracker_ref.add_item(
                role="system",
                content=f"Asked clarifying question: {question_type}",
                agent_name=self.agent_name
            )

        await self.generate_contextual_reply(f"Fråga naturligt: '{question}'")

    @function_tool
    async def collect_contact_info(self, name: str = None, phone: str = None, email: str = None) -> None:
        """Collect contact information step by step"""

        if name and not self.contact_details.name:
            self.contact_details.name = name
            self.conversation_phase = "collecting_phone"

            # Natural follow-up for phone confirmation
            response = "Tack. Vill du bli kontaktad på det här numret?"
            await self.generate_contextual_reply(f"Fråga: '{response}'")

        elif phone and not self.contact_details.phone:
            self.contact_details.phone = phone
            self.conversation_phase = "collecting_email"

            # Ask for email if useful for the category
            if self.call_category and self.call_category.requires_specialist:
                response = "Vilken e-post kan vi använda?"
                await self.generate_contextual_reply(f"Fråga: '{response}'")
            else:
                # Skip email for simple cases
                await self.confirm_details()

        elif email and not self.contact_details.email:
            self.contact_details.email = email
            await self.confirm_details()

        else:
            # Start contact collection
            if not self.contact_details.name:
                self.conversation_phase = "collecting_name"
                response = "Vad heter du?"
                await self.generate_contextual_reply(f"Fråga: '{response}'")

    @function_tool
    async def confirm_details(self) -> None:
        """Confirm collected contact details by reading them back"""

        details = []
        if self.contact_details.name:
            details.append(self.contact_details.name)
        if self.contact_details.phone:
            details.append("detta nummer" if not self.contact_details.phone.startswith('+') else self.contact_details.phone)
        if self.contact_details.email:
            details.append(self.contact_details.email)

        if len(details) >= 2:  # At least name and phone
            confirmation = f"Jag uppfattade: {', '.join(details)}. Stämmer det?"
            self.conversation_phase = "confirming_details"

            if self.tracker_ref:
                self.tracker_ref.add_item(
                    role="system",
                    content=f"Confirming details: {details}",
                    agent_name=self.agent_name
                )

            await self.generate_contextual_reply(f"Bekräfta: '{confirmation}'")
        else:
            # Need more info
            await self.collect_contact_info()

    @function_tool
    async def propose_meeting(self, meeting_type: str = "consultation", urgency: str = "normal") -> None:
        """Propose a meeting or callback based on call category"""

        if self.call_category and self.call_category.requires_specialist:
            if self.call_category.category == "insurance":
                proposal = "Det här verkar kräva en genomgång. Vill du att jag föreslår en tid med en rådgivare?"
            elif self.call_category.category == "solar":
                proposal = "Det här låter som något våra tekniker bör titta på. Vill du att jag bokar en konsultation?"
            else:
                proposal = "Det här verkar kräva ett samtal. Vill du att jag föreslår en tid?"
        else:
            # Simple follow-up
            proposal = "Jag ser till att en kollega kontaktar dig så fort som möjligt."

        self.conversation_phase = "proposing_next_step"

        if self.tracker_ref:
            self.tracker_ref.add_item(
                role="system",
                content=f"Proposed next step: {meeting_type} ({urgency})",
                agent_name=self.agent_name
            )

        await self.generate_contextual_reply(f"Föreslå: '{proposal}'")

    @function_tool
    async def escalate_to_human(self, reason: str, urgency: str = "normal", summary: str = None) -> None:
        """Escalate complex cases to human staff"""

        escalation_responses = {
            "complex": "Det här ärendet kräver mer specialkunskap. Jag vidarebefordrar dig till en kollega.",
            "technical": "Jag kopplar dig till vår tekniska support som kan hjälpa dig bättre.",
            "urgent": "Jag förstår att det här är brådskande. Låt mig se till att du får hjälp direkt."
        }

        response = escalation_responses.get(reason, "Jag vidarebefordrar ditt ärende till rätt person.")

        if self.tracker_ref:
            self.tracker_ref.add_item(
                role="system",
                content=f"Escalating to human: {reason} - {summary}",
                agent_name=self.agent_name
            )

        await self.generate_contextual_reply(f"Eskalera: '{response}'")

    @function_tool
    async def close_conversation(self, summary: str = None) -> None:
        """Close the conversation with a polite summary"""

        # Create natural summary
        parts = []
        if self.call_category:
            parts.append(f"ärende gällande {self.call_category.category}")
        if self.contact_details.name:
            parts.append(f"kontakt till {self.contact_details.name}")

        if parts:
            summary_text = f"Tack, jag har noterat {', '.join(parts)}."
        else:
            summary_text = "Tack för ditt samtal."

        closing = f"{summary_text} En medarbetare återkommer så fort de kan. Är det något mer jag kan hjälpa dig med?"

        self.conversation_phase = "closing"

        if self.tracker_ref:
            self.tracker_ref.add_item(
                role="system",
                content="Conversation closing initiated",
                agent_name=self.agent_name
            )

        await self.generate_contextual_reply(f"Avsluta: '{closing}'")

    def _get_category_questions(self, category: str) -> List[str]:
        """Get relevant follow-up questions for each category"""
        question_sets = {
            "insurance": [
                "Gäller det din nuvarande plan eller en ny?",
                "Handlar det om premien eller täckningen?",
                "Är det något specifikt du vill ändra?"
            ],
            "solar": [
                "Gäller det en befintlig anläggning eller en ny installation?",
                "Handlar det om prestanda eller ett tekniskt problem?",
                "Är det brådskande eller kan det vänta?"
            ],
            "support": [
                "Vad är det som inte fungerar som det ska?",
                "När märkte du problemet första gången?",
                "Har du provat något för att lösa det?"
            ],
            "general": [
                "Vad skulle du vilja veta mer om?",
                "Är det något specifikt du funderar på?",
                "Hur kan vi hjälpa dig bäst?"
            ]
        }
        return question_sets.get(category, question_sets["general"])

    def should_handoff(self, user_input: str) -> tuple[bool, str, str]:
        """Determine if handoff to specialist is needed"""
        if not self.call_category:
            return False, "", ""

        # Check if we need specialist after categorization and contact collection
        if (self.call_category.requires_specialist and
            self.contact_details.name and
            self.conversation_phase in ["confirming_details", "proposing_next_step"]):

            if self.call_category.category == "insurance":
                return True, "InsuranceSpecialist", "Insurance consultation needed"
            elif self.call_category.category == "solar":
                return True, "SolarSpecialist", "Solar installation consultation needed"

        return False, "", ""