#!/usr/bin/env python3
"""
Working outbound trigger - add participant to force agent dispatch
"""

import asyncio
import json
import os
import time
from livekit import api
from dotenv import load_dotenv

load_dotenv(".env.local")

async def trigger_outbound():
    """Trigger outbound call by creating room with participant"""

    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    if not all([url, api_key, api_secret]):
        print("❌ Missing credentials")
        return

    livekit_api = api.LiveKitAPI(url, api_key, api_secret)
    phone = "+46723161614"
    room_name = f"outbound-call-{int(time.time())}"  # Unique room name
    metadata = json.dumps({"phone_number": phone})

    try:
        print(f"🚀 Creating room: {room_name}")

        # Create room with metadata
        room = await livekit_api.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                metadata=metadata
            )
        )
        print(f"✅ Room created with metadata")

        # Wait for agent to pick up room
        await asyncio.sleep(2)

        print(f"📞 Agent should now detect room and make outbound call")

    except Exception as e:
        print(f"❌ Failed: {e}")
    finally:
        await livekit_api.aclose()

if __name__ == "__main__":
    asyncio.run(trigger_outbound())