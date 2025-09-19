"""
Specialist Agents - Category-specific agents for insurance and solar consultations
Implements domain expertise while maintaining conversational flow
"""

import logging
from typing import List, Optional
from livekit.agents import function_tool

# Import base classes from template system
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from agents.base_agent import BaseAgent, AgentConfig

logger = logging.getLogger("specialist-agents")


class InsuranceSpecialist(BaseAgent):
    """Insurance specialist agent for detailed insurance consultations"""

    def __init__(self, config: AgentConfig, tools: List = None, chat_ctx=None):
        insurance_tools = [
            self.assess_insurance_needs,
            self.schedule_consultation,
            self.provide_general_info,
        ]
        if tools:
            insurance_tools.extend(tools)

        super().__init__(config, insurance_tools, chat_ctx)

    def _build_instructions(self) -> str:
        """Build instructions for insurance specialist"""
        return """
Du är en försäkringsspecialist som hjälper kunder med försäkringsfrågor.

EXPERTOMRÅDE: Försäkringar och risktäckning

HUVUDUPPGIFTER:
1. Förstå kundens försäkringsbehov
2. Ställ specifika frågor om nuvarande täckning
3. Identifiera förbättringsmöjligheter
4. Föreslå lämpliga nästa steg (möte, offert, rådgivning)

SAMTALSRIKTLINJER:
- En fråga i taget - korta, riktade frågor
- Fokusera på kundens specifika situation
- Använd naturliga övergångar: "Jag förstår", "Det låter vettigt"
- Var tydlig med begränsningar: "För exakta priser behöver vi ett möte"
- Föreslå konkreta nästa steg

SPECIALKUNSKAP:
- Kan förklara olika typer av försäkringar
- Vet vilka frågor som behövs för en korrekt bedömning
- Kan inte ge exakta priser utan fullständig genomgång

Du är kunnig men inte påträngande. Hjälp kunden förstå vad som behövs för bästa rådgivning.
"""

    async def on_enter(self) -> None:
        """Called when insurance specialist becomes active"""
        if self.tracker_ref:
            self.tracker_ref.add_item(
                role="system",
                content="Insurance specialist activated",
                agent_name=self.agent_name
            )

        intro = "Jag förstår att du vill jämföra försäkringsalternativ. Vad är viktigast för dig att få svar på?"
        await self.generate_contextual_reply(f"Introducera dig: '{intro}'")

    @function_tool
    async def assess_insurance_needs(self, current_coverage: str, concern_area: str = None) -> None:
        """Assess customer's insurance needs and gaps"""

        if concern_area:
            if "premie" in concern_area.lower() or "kostnad" in concern_area.lower():
                response = "För att kunna jämföra kostnader behöver jag veta mer om din nuvarande täckning. Vilken typ av försäkring har du idag?"
            elif "täckning" in concern_area.lower() or "skydd" in concern_area.lower():
                response = "Vad känner du att din nuvarande försäkring inte täcker tillräckligt bra?"
            else:
                response = "Kan du berätta mer om vad som fick dig att fundera på att byta försäkring?"
        else:
            response = "För att ge dig bästa rådgivning behöver jag förstå din nuvarande situation bättre. Vilken typ av försäkring gäller det?"

        if self.tracker_ref:
            self.tracker_ref.add_item(
                role="system",
                content=f"Assessing insurance needs: {current_coverage}, concern: {concern_area}",
                agent_name=self.agent_name
            )

        await self.generate_contextual_reply(f"Fråga: '{response}'")

    @function_tool
    async def schedule_consultation(self, consultation_type: str = "comparison", urgency: str = "normal") -> None:
        """Schedule a detailed insurance consultation"""

        if consultation_type == "comparison":
            proposal = "För att göra en korrekt jämförelse behöver vi gå igenom din situation mer detaljerat. Passar det med ett samtal inom några dagar?"
        elif consultation_type == "review":
            proposal = "Det låter som du skulle ha nytta av en genomgång av hela din försäkringssituation. Vill du boka in det?"
        else:
            proposal = "Jag tror du skulle ha stor nytta av att träffa en av våra rådgivare. Ska jag se över lämpliga tider?"

        if urgency == "high":
            proposal += " Jag kan prioritera detta eftersom det verkar viktigt för dig."

        if self.tracker_ref:
            self.tracker_ref.add_item(
                role="system",
                content=f"Scheduling {consultation_type} consultation, urgency: {urgency}",
                agent_name=self.agent_name
            )

        await self.generate_contextual_reply(f"Föreslå: '{proposal}'")

    @function_tool
    async def provide_general_info(self, topic: str) -> None:
        """Provide general insurance information"""

        info_responses = {
            "process": "Processen börjar med en genomgång av din nuvarande situation, sedan tittar vi på alternativ som passar dina behov bättre.",
            "timeline": "En försäkringsjämförelse tar vanligtvis 30-45 minuter, och du får svar direkt.",
            "cost": "Kostnaden beror helt på din specifika situation. Det vi kan göra är att visa dig vad du skulle spara eller få mer för samma pengar.",
            "coverage": "Täckningen varierar mycket mellan olika försäkringar. Det viktiga är att hitta rätt balans för just dina behov."
        }

        response = info_responses.get(topic, f"Det är en bra fråga om {topic}. För att ge dig korrekt information behöver jag veta lite mer om din situation.")

        await self.generate_contextual_reply(f"Informera: '{response}'")


class SolarSpecialist(BaseAgent):
    """Solar installation specialist for technical and installation consultations"""

    def __init__(self, config: AgentConfig, tools: List = None, chat_ctx=None):
        solar_tools = [
            self.diagnose_solar_issue,
            self.assess_installation_needs,
            self.schedule_technical_visit,
        ]
        if tools:
            solar_tools.extend(tools)

        super().__init__(config, solar_tools, chat_ctx)

    def _build_instructions(self) -> str:
        """Build instructions for solar specialist"""
        return """
Du är en solenergispecialist som hjälper med solcellsanläggningar.

EXPERTOMRÅDE: Solcellsinstallationer och teknisk support

HUVUDUPPGIFTER:
1. Diagnostisera problem med befintliga anläggningar
2. Bedöma behov för nya installationer
3. Förklara tekniska lösningar på ett enkelt sätt
4. Boka tekniska besök när det behövs

SAMTALSRIKTLINJER:
- En fråga i taget - fokusera på det akuta problemet först
- Fråga specifikt om symptom och prestanda
- Förklara tekniska saker enkelt: "Det betyder att..."
- Var tydlig med när ett besök behövs kontra telefonsupport
- Visa entusiasm för solenergi men var realistisk om lösningar

SPECIALKUNSKAP:
- Kan diagnostisera vanliga solcellsproblem
- Vet när teknisk support kan ges per telefon vs på plats
- Förstår installationsprocesser och krav
- Kan förklara energiproduktion och besparingar

Du är tekniskt kunnig men kommunicerar på ett sätt som alla förstår.
"""

    async def on_enter(self) -> None:
        """Called when solar specialist becomes active"""
        if self.tracker_ref:
            self.tracker_ref.add_item(
                role="system",
                content="Solar specialist activated",
                agent_name=self.agent_name
            )

        intro = "Jag förstår att det gäller din solcellsanläggning. Fungerar den inte som den ska?"
        await self.generate_contextual_reply(f"Introducera dig: '{intro}'")

    @function_tool
    async def diagnose_solar_issue(self, issue_description: str, system_age: str = None) -> None:
        """Diagnose solar system issues"""

        issue_lower = issue_description.lower()

        if "producerar inte" in issue_lower or "ingen el" in issue_lower:
            response = "Det låter som ett produktionsproblem. Kan du se några siffror på displayen eller i appen?"
        elif "mindre" in issue_lower or "sämre" in issue_lower:
            response = "Jag förstår att produktionen har minskat. Har du märkt när det började?"
        elif "fel" in issue_lower or "varning" in issue_lower:
            response = "Visas det några felmeddelanden eller varningslampor på systemet?"
        else:
            response = "Kan du beskriva mer specifikt vad som händer med anläggningen?"

        if system_age:
            response += f" Och hur gammal är anläggningen - {system_age}?"

        if self.tracker_ref:
            self.tracker_ref.add_item(
                role="system",
                content=f"Diagnosing solar issue: {issue_description}",
                agent_name=self.agent_name
            )

        await self.generate_contextual_reply(f"Diagnostisera: '{response}'")

    @function_tool
    async def assess_installation_needs(self, property_type: str, energy_usage: str = None) -> None:
        """Assess needs for new solar installation"""

        if property_type:
            if "villa" in property_type.lower() or "hus" in property_type.lower():
                response = "Bra, villa är perfekt för solceller. Vet du ungefär hur mycket el ni använder per år?"
            elif "lägenhet" in property_type.lower():
                response = "För lägenheter behöver vi titta på gemensamma lösningar. Är det en bostadsrättsförening?"
            else:
                response = "Kan du berätta lite mer om fastigheten där du tänker installera solceller?"
        else:
            response = "För att bedöma vad som passar bäst behöver jag veta vilken typ av fastighet det gäller?"

        if energy_usage:
            response += " Det hjälper oss att dimensionera anläggningen rätt."

        if self.tracker_ref:
            self.tracker_ref.add_item(
                role="system",
                content=f"Assessing installation needs: {property_type}, usage: {energy_usage}",
                agent_name=self.agent_name
            )

        await self.generate_contextual_reply(f"Bedöm: '{response}'")

    @function_tool
    async def schedule_technical_visit(self, visit_type: str = "inspection", urgency: str = "normal") -> None:
        """Schedule technical visit for solar issues"""

        if visit_type == "inspection":
            proposal = "Det här verkar kräva att någon tittar på anläggningen på plats. Vill du att jag bokar en tekniker?"
        elif visit_type == "installation_assessment":
            proposal = "För att ge dig en korrekt offert behöver vi göra en platsbesiktning. Passar det inom några dagar?"
        elif visit_type == "repair":
            proposal = "Det här problemet kräver troligtvis en reparation på plats. Ska jag boka in en tekniker?"
        else:
            proposal = "Jag tror det bästa är om en av våra tekniker kommer och tittar. Vill du att jag arrangerar det?"

        if urgency == "high":
            proposal = "Det här verkar brådskande. " + proposal + " Jag kan se om vi kan prioritera det."

        if self.tracker_ref:
            self.tracker_ref.add_item(
                role="system",
                content=f"Scheduling {visit_type} visit, urgency: {urgency}",
                agent_name=self.agent_name
            )

        await self.generate_contextual_reply(f"Boka: '{proposal}'")