#!/usr/bin/env python3.11
"""
Test script to check existing config and see if we can update it.
"""

import asyncio
import os
from dotenv import load_dotenv
from hume import AsyncHumeClient

async def check_existing_config():
    """Check the existing config that's being used."""
    load_dotenv()
    api_key = os.getenv("HUME_API_KEY")
    existing_config_id = "34e1fd90-c47d-430a-97b8-00cef88adaf5"  # From the logs
    
    if not api_key:
        print("❌ HUME_API_KEY not found")
        return
    
    client = AsyncHumeClient(api_key=api_key)
    
    try:
        # List configs to see what's available
        print("📋 Listing existing configs...")
        configs = await client.empathic_voice.configs.list_configs()
        
        async for config in configs:
            print(f"  📄 Config: {config.name} (ID: {config.id})")
            if hasattr(config, 'tools') and config.tools:
                print(f"      🔧 Tools: {len(config.tools)}")
            if hasattr(config, 'prompt') and config.prompt:
                prompt_preview = config.prompt.text[:100] + "..." if len(config.prompt.text) > 100 else config.prompt.text
                print(f"      📝 Prompt preview: {prompt_preview}")
        
        # Check the specific config being used
        print(f"\n🔍 Checking existing config: {existing_config_id}")
        try:
            # Get the latest version of the config
            versions = await client.empathic_voice.configs.list_config_versions(existing_config_id)
            latest_version = None
            async for version in versions:
                if latest_version is None or version.version > latest_version.version:
                    latest_version = version
            
            if latest_version:
                print(f"📋 Latest version: {latest_version.version}")
                print(f"📝 Config name: {latest_version.name}")
                if hasattr(latest_version, 'tools') and latest_version.tools:
                    print(f"🔧 Tools available: {len(latest_version.tools)}")
                    for tool in latest_version.tools:
                        print(f"   - {tool.name}: {tool.description[:50]}...")
                else:
                    print("❌ No tools in this config")
                
                if hasattr(latest_version, 'prompt') and latest_version.prompt:
                    prompt_text = latest_version.prompt.text
                    print(f"📝 Prompt length: {len(prompt_text)} characters")
                    print(f"🎯 Contains tool enforcement: {'MUST call' in prompt_text}")
                    print(f"💰 Contains settlement triggers: {'twenty-five thousand' in prompt_text}")
                else:
                    print("❌ No prompt in this config")
            else:
                print("❌ Could not find config versions")
                
        except Exception as e:
            print(f"❌ Error checking config: {e}")
    
    except Exception as e:
        print(f"❌ Error listing configs: {e}")

async def main():
    """Main function."""
    print("🔍 Checking existing EVI configurations...")
    await check_existing_config()

if __name__ == "__main__":
    asyncio.run(main())