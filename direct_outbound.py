#!/usr/bin/env python3
"""
Direct outbound SIP call trigger - bypasses room creation
Uses your agent's built-in outbound SIP calling mechanism
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment
load_dotenv(".env.local")

def trigger_direct_outbound():
    """Trigger outbound call using LiveKit SIP API directly"""

    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    if not all([url, api_key, api_secret]):
        print("❌ Missing LiveKit credentials")
        return

    # Your verified working trunk and agent setup
    trunk_id = "ST_SigM7KTZGNok"
    phone = "+46723161614"

    # Create room with outbound metadata (this should trigger your agent)
    room_name = f"outbound-direct-{phone.replace('+', '')}"

    print(f"🚀 Creating direct outbound call")
    print(f"📞 Phone: {phone}")
    print(f"📡 Trunk: {trunk_id}")
    print(f"🏠 Room: {room_name}")

    # Use REST API to create SIP call directly
    sip_url = f"{url.replace('wss://', 'https://')}/twirp/livekit.SIPService/CreateSIPParticipant"

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}:{api_secret}'
    }

    payload = {
        "room_name": room_name,
        "sip_trunk_id": trunk_id,
        "sip_call_to": phone,
        "participant_identity": phone,
        "wait_until_answered": True
    }

    try:
        response = requests.post(sip_url, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Direct SIP call created:")
            print(f"   Participant ID: {result.get('participant_id', 'N/A')}")
            print(f"   SIP Call ID: {result.get('sip_call_id', 'N/A')}")
            print(f"   Room: {result.get('room_name', room_name)}")
        else:
            print(f"❌ SIP call failed: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    trigger_direct_outbound()