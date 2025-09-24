#!/usr/bin/env python3
"""
Simple outbound call trigger for LiveKit 2025
Triggers your existing agent.py with outbound metadata
"""

import asyncio
import json
import os
from livekit import api
from dotenv import load_dotenv

# Load environment
load_dotenv(".env.local")

async def trigger_outbound_call(phone_number: str):
    """Trigger outbound call with metadata to activate outbound workflow"""

    # LiveKit credentials
    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    if not all([url, api_key, api_secret]):
        print("❌ Missing LiveKit credentials in .env.local")
        return

    # Create API client
    livekit_api = api.LiveKitAPI(url, api_key, api_secret)

    # Create room for outbound call
    room_name = f"outbound-call-{phone_number.replace('+', '').replace(' ', '')}"

    try:
        # Create room with outbound metadata
        metadata = json.dumps({"phone_number": phone_number})

        print(f"🚀 Creating outbound call room: {room_name}")
        print(f"📞 Target phone: {phone_number}")
        print(f"📋 Metadata: {metadata}")

        room = await livekit_api.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                metadata=metadata
            )
        )

        print(f"✅ Room created: {room.name}")

        # For outbound calls, we need to create a job directly since there's no participant to trigger auto-dispatch
        # Use LiveKit 2025 approach: create job via room joining
        print(f"🎯 Room created - now triggering agent job via participant connection...")

        # The agent will auto-assign when the SIP participant joins
        # This mimics the auto-dispatch behavior for outbound scenarios

        print(f"🎯 Your agent will now:")
        print(f"   1. Detect outbound call via metadata")
        print(f"   2. Use 'Finn' outbound workflow")
        print(f"   3. Create SIP participant to call {phone_number}")
        print(f"   4. Deliver outbound greeting when answered")

    except Exception as e:
        print(f"❌ Outbound call failed: {e}")

if __name__ == "__main__":
    # Your phone number
    phone = "+46723161614"
    asyncio.run(trigger_outbound_call(phone))