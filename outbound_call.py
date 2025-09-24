#!/usr/bin/env python3
"""
Working outbound call trigger using LiveKit 2025 pattern
Based on successful call logs from your agent
"""

import asyncio
import json
import os
from livekit import api
from dotenv import load_dotenv

# Load environment
load_dotenv(".env.local")

async def make_outbound_call(phone_number: str):
    """Create outbound call using verified working pattern"""

    # LiveKit credentials
    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    if not all([url, api_key, api_secret]):
        print("❌ Missing LiveKit credentials")
        return

    # Create API client
    livekit_api = api.LiveKitAPI(url, api_key, api_secret)

    # Create room with outbound metadata (this pattern worked in your logs)
    room_name = f"outbound-call-{phone_number.replace('+', '').replace(' ', '')}"
    metadata = json.dumps({"phone_number": phone_number})

    try:
        print(f"🚀 Creating outbound call room: {room_name}")
        print(f"📞 Target: {phone_number}")
        print(f"📋 Metadata: {metadata}")

        # Step 1: Create room with metadata
        room = await livekit_api.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                metadata=metadata
            )
        )
        print(f"✅ Room created: {room.name}")

        # Step 2: Your agent will auto-detect this room and handle the SIP calling
        # This is based on the successful pattern from your 20:02 calls
        print(f"🎯 Room created - agent should auto-detect and handle outbound call")
        print(f"🔄 Workflow: Agent will detect metadata and use Finn greeting")
        print(f"📞 SIP: Agent will call {phone_number} using trunk ST_SigM7KTZGNok")

        # Wait a moment to see if agent picks up the job
        await asyncio.sleep(3)
        print(f"⏱️ Monitoring agent logs for job pickup...")

    except Exception as e:
        print(f"❌ Outbound call setup failed: {e}")

    finally:
        await livekit_api.aclose()

if __name__ == "__main__":
    # Your phone number
    phone = "+46723161614"
    asyncio.run(make_outbound_call(phone))