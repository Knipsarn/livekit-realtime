#!/usr/bin/env python3
"""
Script to create a pre-recorded greeting audio file using OpenAI TTS with cedar voice.
This ensures consistent voice quality and eliminates streaming delays at call start.
"""

import os
import sys
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")
load_dotenv()

def create_greeting_audio():
    """Create pre-recorded greeting audio using OpenAI TTS"""

    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # The greeting message from samuel-agent.md
    greeting_text = "Hej, du har nått Samuel. Jag är Jim, hans assistent. Han kan inte svara just nu, men jag hjälper gärna till att ta ett meddelande. Vem pratar jag med?"

    print(f"Creating greeting audio with text: {greeting_text}")

    try:
        # Generate speech using OpenAI TTS with cedar voice
        response = client.audio.speech.create(
            model="tts-1-hd",  # High quality model
            voice="cedar",     # Same voice as used in realtime
            input=greeting_text,
            response_format="wav"  # WAV format for compatibility
        )

        # Ensure assets directory exists
        assets_dir = Path(__file__).parent.parent / "assets"
        assets_dir.mkdir(exist_ok=True)

        # Save the audio file
        greeting_path = assets_dir / "greeting.wav"
        with open(greeting_path, "wb") as f:
            f.write(response.content)

        print(f"Greeting audio created successfully: {greeting_path}")
        print(f"File size: {greeting_path.stat().st_size} bytes")

        return str(greeting_path)

    except Exception as e:
        print(f"Error creating greeting audio: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_greeting_audio()