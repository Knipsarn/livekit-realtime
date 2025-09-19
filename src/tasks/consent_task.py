"""
Consent Collection Task - Structured task for collecting recording consent
Demonstrates task-based workflow components
"""

import logging
from livekit.agents import AgentTask, function_tool

logger = logging.getLogger("consent-task")


class ConsentCollectionTask(AgentTask[bool]):
    """
    Task for collecting call recording consent
    Returns True if consent given, False if denied
    """

    def __init__(self, chat_ctx=None, language: str = "English"):
        self.language = language.lower()

        if self.language in ["svenska", "swedish"]:
            instructions = """
Du ska fråga om tillstånd att spela in samtalet för kvalitetssäkring och utbildning.
Var tydlig, professionell och respektfull.
Förklara att de kan tacka nej och att samtalet fortfarande kan fortsätta.
"""
        else:
            instructions = """
You need to ask for permission to record the call for quality assurance and training purposes.
Be clear, professional, and respectful.
Explain that they can decline and the call can still continue.
"""

        super().__init__(
            instructions=instructions,
            chat_ctx=chat_ctx,
        )

    async def on_enter(self) -> None:
        """Start the consent collection process"""
        if self.language in ["svenska", "swedish"]:
            consent_request = """
Hej! Innan vi fortsätter, behöver jag fråga om du är okej med att vi spelar in det här samtalet för kvalitetssäkring och utbildningsändamål.
Du kan såklart säga nej, och vi kan fortsätta samtalet ändå.
Är det okej om vi spelar in?
"""
        else:
            consent_request = """
Hi! Before we continue, I need to ask if you're comfortable with us recording this call for quality assurance and training purposes.
You're absolutely free to decline, and we can still continue our conversation.
Is it okay if we record this call?
"""

        await self.session.generate_reply(instructions=f"Say exactly: {consent_request}")

    @function_tool
    async def consent_given(self) -> None:
        """Call this when the user gives consent to record"""
        logger.info("Recording consent granted")

        if self.language in ["svenska", "swedish"]:
            response = "Tack så mycket! Inspelningen påbörjas nu. Hur kan jag hjälpa dig idag?"
        else:
            response = "Thank you! Recording will now begin. How can I help you today?"

        await self.session.generate_reply(instructions=f"Say: {response}")
        self.complete(True)

    @function_tool
    async def consent_denied(self) -> None:
        """Call this when the user denies consent to record"""
        logger.info("Recording consent denied")

        if self.language in ["svenska", "swedish"]:
            response = "Inga problem alls! Vi kommer inte att spela in samtalet. Hur kan jag hjälpa dig idag?"
        else:
            response = "No problem at all! We won't record the call. How can I help you today?"

        await self.session.generate_reply(instructions=f"Say: {response}")
        self.complete(False)

    @function_tool
    async def unclear_response(self) -> None:
        """Call this when the user's response is unclear"""
        if self.language in ["svenska", "swedish"]:
            clarification = """
Jag är inte helt säker på vad du svarade.
Kan du säga 'ja' om det är okej att vi spelar in samtalet, eller 'nej' om du föredrar att vi inte gör det?
"""
        else:
            clarification = """
I'm not entirely sure what you said.
Could you please say 'yes' if it's okay to record the call, or 'no' if you'd prefer we don't record?
"""

        await self.session.generate_reply(instructions=f"Say: {clarification}")


class DataCollectionConsentTask(AgentTask[bool]):
    """
    Task for collecting consent to store personal data
    More comprehensive than recording consent
    """

    def __init__(self, chat_ctx=None, language: str = "English", data_types: str = "contact information"):
        self.language = language.lower()
        self.data_types = data_types

        if self.language in ["svenska", "swedish"]:
            instructions = f"""
Du ska fråga om tillstånd att lagra {data_types} enligt GDPR.
Förklara vad informationen används till och hur länge den lagras.
Var tydlig med att de kan tacka nej.
"""
        else:
            instructions = f"""
You need to ask for permission to store {data_types} in compliance with data protection regulations.
Explain what the information will be used for and how long it will be stored.
Be clear that they can decline.
"""

        super().__init__(
            instructions=instructions,
            chat_ctx=chat_ctx,
        )

    async def on_enter(self) -> None:
        """Start the data consent collection process"""
        if self.language in ["svenska", "swedish"]:
            consent_request = f"""
För att kunna hjälpa dig bäst behöver jag samla in {self.data_types}.
Denna information kommer endast användas för att kunna kontakta dig och följa upp ditt ärende.
Vi lagrar informationen säkert och du kan när som helst be oss ta bort den.
Är det okej att jag samlar in denna information?
"""
        else:
            consent_request = f"""
To help you best, I need to collect {self.data_types}.
This information will only be used to contact you and follow up on your request.
We store information securely and you can ask us to delete it at any time.
Is it okay for me to collect this information?
"""

        await self.session.generate_reply(instructions=f"Say: {consent_request}")

    @function_tool
    async def data_consent_given(self) -> None:
        """Call this when user gives consent for data collection"""
        logger.info("Data collection consent granted")

        if self.language in ["svenska", "swedish"]:
            response = "Tack! Jag kommer att samla in den information som behövs. Vad heter du?"
        else:
            response = "Thank you! I'll collect the information needed. What's your name?"

        await self.session.generate_reply(instructions=f"Say: {response}")
        self.complete(True)

    @function_tool
    async def data_consent_denied(self) -> None:
        """Call this when user denies consent for data collection"""
        logger.info("Data collection consent denied")

        if self.language in ["svenska", "swedish"]:
            response = "Jag förstår. Jag kommer inte att samla in din personliga information. Hur kan jag hjälpa dig ändå?"
        else:
            response = "I understand. I won't collect your personal information. How can I still help you?"

        await self.session.generate_reply(instructions=f"Say: {response}")
        self.complete(False)