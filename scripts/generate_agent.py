#!/usr/bin/env python3
"""
🤖 LiveKit Agent Generation Wizard
Interactive tool to create fully configured voice agents from templates
"""

import os
import sys
import yaml
import shutil
import argparse
from pathlib import Path
from typing import Dict, Any, List
import re


class AgentWizard:
    """Interactive wizard for agent creation"""

    def __init__(self):
        self.config = {}
        self.template_dir = Path(__file__).parent.parent
        self.output_dir = None

    def run(self):
        """Run the interactive wizard"""
        self.print_header()
        self.collect_basic_info()
        self.collect_conversation_settings()
        self.collect_features()
        self.collect_prompt_settings()
        self.collect_integrations()
        self.generate_agent()

    def print_header(self):
        """Print welcome header"""
        print("\n" + "=" * 60)
        print("🤖 LiveKit Voice Agent Generation Wizard")
        print("=" * 60)
        print("\nThis wizard will help you create a fully configured voice agent.")
        print("Press Enter to use default values shown in [brackets].\n")

    def collect_basic_info(self):
        """Step 1: Basic Information"""
        print("\n📋 Step 1: Basic Information")
        print("-" * 40)

        self.config["agent"] = {
            "name": self.ask("Agent name", "Assistant"),
            "owner": self.ask("Owner/Business name", "My Company"),
            "language": self.ask_choice("Language", ["English", "Svenska", "Español", "Français", "Custom"], "English"),
            "voice": self.ask_choice("Voice", ["cedar", "nova", "marin", "alloy"], "cedar"),
            "personality_traits": self.ask("Personality traits", "professional, friendly, helpful")
        }

        # Custom language input
        if self.config["agent"]["language"] == "Custom":
            self.config["agent"]["language"] = self.ask("Enter custom language")

    def collect_conversation_settings(self):
        """Step 2: Conversation Settings"""
        print("\n💬 Step 2: Conversation Settings")
        print("-" * 40)

        style = self.ask_choice(
            "Conversation style",
            ["formal", "casual", "consultative", "medical", "legal"],
            "consultative"
        )

        # Generate appropriate greeting based on style and language
        default_greeting = self.generate_greeting(
            self.config["agent"]["language"],
            style,
            self.config["agent"]["owner"]
        )

        self.config["conversation"] = {
            "first_message": self.ask_multiline("First message/greeting", default_greeting),
            "conversation_style": style,
            "response_length": self.ask_choice("Response length", ["short", "medium", "detailed"], "medium"),
            "use_prerecorded_greeting": self.ask_bool("Use pre-recorded audio greeting?", False)
        }

    def collect_features(self):
        """Step 3: Feature Selection"""
        print("\n⚙️ Step 3: Feature Selection")
        print("-" * 40)
        print("Select which features to enable:")

        # Core features
        print("\n🔧 Core Features:")
        memory_enabled = self.ask_bool("✓ Memory System (track caller information)", True)
        safety_enabled = self.ask_bool("✓ Safety Features (call limits, timeout detection)", True)
        webhook_enabled = self.ask_bool("✓ Webhook Integration (send conversation data)", False)

        # Advanced features
        print("\n🚀 Advanced Features:")
        workflow_type = self.ask_choice(
            "Workflow type",
            ["single_agent", "multi_agent", "task_based", "hybrid"],
            "single_agent"
        )

        # Memory configuration
        if memory_enabled:
            self.config["memory"] = {
                "enabled": True,
                "track_caller_info": True,
                "auto_extract_phone": self.ask_bool("Auto-extract phone from SIP?", True),
                "persist_conversation": True,
                "tracked_fields": ["name", "phone", "email", "purpose", "urgency"]
            }
        else:
            self.config["memory"] = {"enabled": False}

        # Safety configuration
        if safety_enabled:
            self.config["safety"] = {
                "enabled": True,
                "max_call_duration": int(self.ask("Maximum call duration (seconds)", "600")),
                "inactivity_timeout": int(self.ask("Inactivity timeout (seconds)", "30")),
                "participant_disconnect_detection": True
            }
        else:
            self.config["safety"] = {"enabled": False}

        # Workflow configuration
        self.config["workflow"] = {
            "type": workflow_type,
            "enable_handoffs": workflow_type in ["multi_agent", "hybrid"],
            "max_handoffs": 3,
            "context_preservation": True
        }

        # Task configuration
        if workflow_type in ["task_based", "hybrid"]:
            self.config["tasks"] = {
                "information_gathering": {
                    "enabled": True,
                    "required_fields": ["name", "phone"],
                    "optional_fields": ["email", "company"],
                    "validation_strict": False
                }
            }
        else:
            self.config["tasks"] = {
                "information_gathering": {"enabled": False}
            }

        # Webhook configuration
        if webhook_enabled:
            self.config["integrations"] = {
                "webhook": {
                    "enabled": True,
                    "url": self.ask("Webhook URL (or set via WEBHOOK_URL env)", ""),
                    "events": ["call_start", "call_end", "data_collected"]
                }
            }
        else:
            self.config["integrations"] = {"webhook": {"enabled": False}}

    def collect_prompt_settings(self):
        """Step 4: Prompt Configuration"""
        print("\n📝 Step 4: Prompt Configuration")
        print("-" * 40)

        use_case = self.ask_choice(
            "Primary use case",
            ["missed_calls", "customer_support", "sales", "scheduling", "technical_support", "general"],
            "general"
        )

        industry = self.ask_choice(
            "Industry",
            ["general", "healthcare", "finance", "retail", "technology", "real_estate", "legal"],
            "general"
        )

        template_choice = self.ask_choice(
            "Prompt template",
            ["conversational", "formal", "technical", "custom"],
            "conversational"
        )

        prompt_config = {
            "template": template_choice,
            "use_case": use_case,
            "industry": industry,
            "rules": {
                "allow_interruptions": self.ask_bool("Allow interruptions?", True),
                "ask_one_question": self.ask_bool("Ask one question at a time?", True),
                "confirm_information": self.ask_bool("Confirm information by repeating?", True),
                "use_fillers": self.ask_bool("Use natural fillers (um, okay)?", False)
            }
        }

        if template_choice == "custom":
            print("\nEnter custom prompt (press Enter twice to finish):")
            prompt_config["custom_prompt"] = self.ask_multiline("Custom prompt")

        self.config["prompt"] = prompt_config

    def collect_integrations(self):
        """Step 5: Additional Integrations"""
        print("\n🔌 Step 5: Additional Integrations (Optional)")
        print("-" * 40)

        if self.ask_bool("Configure telephony settings?", True):
            self.config["integrations"]["telephony"] = {
                "enabled": True,
                "provider": self.ask_choice("Provider", ["livekit", "telnyx", "twilio"], "livekit"),
                "transcription": True,
                "recording": self.ask_bool("Enable call recording?", False)
            }

        # Model configuration
        self.config["model"] = {
            "provider": "openai",
            "name": "gpt-realtime",
            "temperature": float(self.ask("Model temperature (0.1-1.0)", "0.7")),
            "max_tokens": 150
        }

    def generate_agent(self):
        """Generate the agent files"""
        print("\n🚀 Generating Agent...")
        print("-" * 40)

        # Create output directory
        agent_name = self.config["agent"]["name"].lower().replace(" ", "_")
        self.output_dir = self.template_dir / f"agents/{agent_name}"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Generate config file
        self.generate_config_file()

        # Copy template agent
        self.copy_agent_template()

        # Generate environment template
        self.generate_env_template()

        # Generate README
        self.generate_readme()

        # Generate livekit.toml
        self.generate_livekit_toml()

        print(f"\n✅ Agent successfully generated at: {self.output_dir}")
        print("\n📋 Next steps:")
        print("1. cd " + str(self.output_dir))
        print("2. cp .env.template .env")
        print("3. Edit .env with your API keys")
        print("4. pip install -r requirements.txt")
        print("5. lk agent deploy")
        print("\n🎉 Your agent is ready to deploy!")

    def generate_config_file(self):
        """Generate the agent configuration file"""
        config_path = self.output_dir / "config/agent.config.yaml"
        config_path.parent.mkdir(exist_ok=True)

        with open(config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)

        print(f"✓ Generated configuration: {config_path}")

    def copy_agent_template(self):
        """Copy and configure the agent template"""
        template_src = self.template_dir / "src/agent_template.py"
        agent_dest = self.output_dir / "src/agent.py"
        agent_dest.parent.mkdir(exist_ok=True)

        shutil.copy2(template_src, agent_dest)
        print(f"✓ Generated agent code: {agent_dest}")

        # Copy requirements
        req_src = self.template_dir / "requirements.txt"
        req_dest = self.output_dir / "requirements.txt"
        shutil.copy2(req_src, req_dest)

    def generate_env_template(self):
        """Generate environment variable template"""
        env_template = """# LiveKit Configuration
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# OpenAI Configuration
OPENAI_API_KEY=your_openai_key

# Optional: Webhook URL (if not set in config)
# WEBHOOK_URL=https://your-webhook-endpoint.com

# Optional: Other integrations
# GOOGLE_CALENDAR_API_KEY=your_key
# CRM_API_KEY=your_key
"""

        env_path = self.output_dir / ".env.template"
        with open(env_path, 'w') as f:
            f.write(env_template)

        print(f"✓ Generated environment template: {env_path}")

    def generate_readme(self):
        """Generate README documentation"""
        readme_content = f"""# {self.config['agent']['name']} Voice Agent

## Overview
This is a LiveKit voice agent configured for {self.config['agent']['owner']}.

### Configuration
- **Language:** {self.config['agent']['language']}
- **Voice:** {self.config['agent']['voice']}
- **Style:** {self.config['conversation']['conversation_style']}
- **Use Case:** {self.config['prompt']['use_case']}

### Features Enabled
- Memory System: {self.config['memory']['enabled']}
- Safety Features: {self.config['safety']['enabled']}
- Webhook Integration: {self.config.get('integrations', {}).get('webhook', {}).get('enabled', False)}
- Workflow Type: {self.config['workflow']['type']}

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.template .env
   # Edit .env with your API keys
   ```

3. **Deploy the agent:**
   ```bash
   lk agent deploy
   ```

## Testing

Call your agent using the phone number provided by LiveKit after deployment.

## Customization

Edit `config/agent.config.yaml` to modify agent behavior and features.

Generated with LiveKit Agent Template System 🤖
"""

        readme_path = self.output_dir / "README.md"
        with open(readme_path, 'w') as f:
            f.write(readme_content)

        print(f"✓ Generated documentation: {readme_path}")

    def generate_livekit_toml(self):
        """Generate LiveKit configuration"""
        toml_content = f"""[agent]
entrypoint_fnc = "src.agent:entrypoint"

[agent.environment]
AGENT_NAME = "{self.config['agent']['name']}"
"""

        toml_path = self.output_dir / "livekit.toml"
        with open(toml_path, 'w') as f:
            f.write(toml_content)

        print(f"✓ Generated LiveKit config: {toml_path}")

    # Helper methods
    def ask(self, prompt: str, default: str = "") -> str:
        """Ask for user input with default"""
        if default:
            response = input(f"{prompt} [{default}]: ").strip()
            return response if response else default
        else:
            response = input(f"{prompt}: ").strip()
            while not response:
                response = input(f"{prompt} (required): ").strip()
            return response

    def ask_bool(self, prompt: str, default: bool = False) -> bool:
        """Ask for boolean input"""
        default_str = "Y" if default else "N"
        opposite = "n" if default else "y"
        response = input(f"{prompt} [{default_str}/{opposite}]: ").strip().lower()

        if not response:
            return default
        return response in ['y', 'yes', 'true', '1']

    def ask_choice(self, prompt: str, choices: List[str], default: str = None) -> str:
        """Ask for choice from list"""
        print(f"\n{prompt}:")
        for i, choice in enumerate(choices, 1):
            default_mark = " (default)" if choice == default else ""
            print(f"  [{i}] {choice}{default_mark}")

        while True:
            response = input(f"Select [1-{len(choices)}]: ").strip()

            if not response and default:
                return default

            try:
                idx = int(response) - 1
                if 0 <= idx < len(choices):
                    return choices[idx]
            except ValueError:
                pass

            print("Invalid selection. Please try again.")

    def ask_multiline(self, prompt: str, default: str = "") -> str:
        """Ask for multiline input"""
        if default:
            print(f"{prompt} (press Enter to use default):")
            print(f"Default: {default}")
            response = input("Enter new value or press Enter for default: ").strip()
            return response if response else default

        print(f"{prompt} (press Enter twice to finish):")
        lines = []
        while True:
            line = input()
            if not line and lines:
                break
            lines.append(line)
        return "\n".join(lines)

    def generate_greeting(self, language: str, style: str, owner: str) -> str:
        """Generate appropriate greeting based on settings"""
        greetings = {
            "English": {
                "formal": f"Good day. Thank you for calling {owner}. How may I assist you today?",
                "casual": f"Hi there! Thanks for calling {owner}. What can I help you with?",
                "consultative": f"Hello, thank you for calling {owner}. How can I help you today?",
                "medical": f"Hello, you've reached {owner}. How may I assist you with your healthcare needs?",
                "legal": f"Good day. You've reached {owner} legal services. How may I direct your call?"
            },
            "Svenska": {
                "formal": f"God dag. Tack för att du ringer {owner}. Hur kan jag hjälpa dig?",
                "casual": f"Hej! Tack för att du ringer {owner}. Vad kan jag hjälpa dig med?",
                "consultative": f"Hej, tack för att du ringde {owner}. Hur kan jag hjälpa dig idag?",
                "medical": f"Hej, du har kommit till {owner}. Hur kan jag hjälpa dig med dina vårdbehov?",
                "legal": f"God dag. Du har ringt {owner} juridiska tjänster. Hur kan jag hjälpa dig?"
            }
        }

        # Default to English consultative if not found
        return greetings.get(language, greetings["English"]).get(
            style,
            f"Hello, thank you for calling {owner}. How can I help you today?"
        )


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="LiveKit Agent Generation Wizard")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode with minimal questions"
    )
    parser.add_argument(
        "--config",
        help="Load configuration from file instead of interactive"
    )

    args = parser.parse_args()

    wizard = AgentWizard()

    if args.config:
        # Load from config file
        with open(args.config, 'r') as f:
            wizard.config = yaml.safe_load(f)
        wizard.generate_agent()
    else:
        # Run interactive wizard
        wizard.run()


if __name__ == "__main__":
    main()