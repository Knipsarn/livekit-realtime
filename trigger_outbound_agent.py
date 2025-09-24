#!/usr/bin/env python3
"""
Trigger outbound calls using the new robert-demo architecture
"""

import asyncio
import json
import os
import time
from livekit import api
from dotenv import load_dotenv

load_dotenv(".env.local")

async def trigger_outbound():
    """Trigger outbound call using outbound agent architecture"""

    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    if not all([url, api_key, api_secret]):
        print("❌ Missing credentials")
        return

    livekit_api = api.LiveKitAPI(url, api_key, api_secret)
    phone = "+46723161614"
    room_name = f"outbound-call-{int(time.time())}"
    metadata = json.dumps({"phone_number": phone})

    try:
        print(f"🚀 Creating room with outbound agent architecture: {room_name}")

        # Create room with metadata for outbound calling
        room = await livekit_api.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                metadata=metadata
            )
        )
        print(f"✅ Room created with outbound metadata")

        # Wait for agent to pick up room and make outbound call
        await asyncio.sleep(2)

        print(f"📞 Outbound agent should now detect room and make call using robert-demo architecture")

    except Exception as e:
        print(f"❌ Failed: {e}")
    finally:
        await livekit_api.aclose()

if __name__ == "__main__":
    asyncio.run(trigger_outbound())