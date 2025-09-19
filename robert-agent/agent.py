#!/usr/bin/env python3
"""
Robert's Conversational Reception Agent
Sophisticated call handling agent with natural conversation flow

Features:
- Natural Swedish conversation
- Intelligent call categorization
- Specialist routing (Insurance, Solar)
- One question at a time principle
- Contact collection and confirmation
- Meeting proposal and escalation
- Graceful interruption handling

Generated from LiveKit Agent Template System
"""

import asyncio
import logging
from livekit.agents import JobContext, WorkerOptions, cli

# Import our conversational workflow
from src.workflows.robert_workflow import entrypoint

logger = logging.getLogger("robert-conversational-agent")

if __name__ == "__main__":
    # Configure logging for natural conversation debugging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting Robert's Conversational Reception Agent")
    logger.info("Features: Natural conversation, intelligent routing, Swedish language")

    # Run the conversational agent
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))