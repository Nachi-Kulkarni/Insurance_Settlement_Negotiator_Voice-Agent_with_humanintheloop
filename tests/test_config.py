#!/usr/bin/env python3.11
"""
Test script to verify EVI config creation with tools works properly.
"""

import asyncio
import os
import logging
from dotenv import load_dotenv
from hume import AsyncHumeClient
from hume.empathic_voice.types import PostedConfigPromptSpec, PostedUserDefinedToolSpec, VoiceName
from force_tool_prompt import get_force_tool_prompt
from evi_config import EVIConfigManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_config_creation():
    """Test creating a proper EVI config with tools."""
    load_dotenv()
    api_key = os.getenv("HUME_API_KEY")
    
    if not api_key:
        print("❌ HUME_API_KEY not found")
        return False
    
    client = AsyncHumeClient(api_key=api_key)
    config_manager = EVIConfigManager()
    
    try:
        print("🚀 Testing EVI config creation...")
        
        # Get the force tool prompt
        prompt = get_force_tool_prompt()
        print(f"📝 Prompt length: {len(prompt)} characters")
        print(f"🎯 Contains tool enforcement: {'MUST call calculate_settlement_offer' in prompt}")
        
        # Get tools
        config = config_manager.create_full_config()
        tools = config['tools']
        print(f"🔧 Tools available: {len(tools)}")
        
        # Create essential tools for EVI
        essential_tools = []
        for tool in tools:
            if tool['name'] in ['calculate_settlement_offer', 'lookup_claim', 'escalate_to_specialist']:
                hume_tool = PostedUserDefinedToolSpec(
                    id=tool['name'],
                    name=tool['name'],
                    description=tool['description'],
                    parameters=tool['parameters']
                )
                essential_tools.append(hume_tool)
                print(f"  ✅ Added tool: {tool['name']}")
        
        # Try different voice specifications
        print("🎵 Trying voice specification...")
        
        # Try with just a string name (most common approach)
        try:
            new_config = await client.empathic_voice.configs.create_config(
                name=f"Portia Test Config Tool Enforced",
                prompt=PostedConfigPromptSpec(text=prompt),
                tools=essential_tools,
                voice="ITO",  # Simple string approach
                evi_version="3"
            )
        except Exception as e1:
            print(f"String voice failed: {e1}")
            # Try with VoiceId
            try:
                from hume.empathic_voice.types import VoiceId
                new_config = await client.empathic_voice.configs.create_config(
                    name=f"Portia Test Config Tool Enforced",
                    prompt=PostedConfigPromptSpec(text=prompt),
                    tools=essential_tools,
                    voice=VoiceId(id="9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"),  # Sample voice ID
                    evi_version="3"
                )
            except Exception as e2:
                print(f"VoiceId failed: {e2}")
                # Try without voice (maybe it's optional?)
                new_config = await client.empathic_voice.configs.create_config(
                    name=f"Portia Test Config Tool Enforced",
                    prompt=PostedConfigPromptSpec(text=prompt),
                    tools=essential_tools,
                    evi_version="3"
                )
        
        print(f"✅ SUCCESS: Config created with ID: {new_config.id}")
        print(f"📋 Config name: {new_config.name}")
        print(f"🔧 Tools included: {len(essential_tools)}")
        print(f"🎯 This config should now FORCE tool usage for settlements!")
        
        return new_config.id
        
    except Exception as e:
        print(f"❌ Config creation failed: {e}")
        return False

async def main():
    """Main test function."""
    print("🧪 Testing EVI config creation with tool enforcement...")
    config_id = await test_config_creation()
    
    if config_id:
        print(f"\n🎉 SUCCESS! Use this config ID: {config_id}")
        print("💡 You can now set HUME_CONFIG_ID to this value to use the tool-enforced config")
    else:
        print("\n❌ Test failed - config creation didn't work")

if __name__ == "__main__":
    asyncio.run(main())