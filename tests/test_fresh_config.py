#!/usr/bin/env python3
"""
Test script to create a fresh EVI config with mandatory tool usage.
"""

import asyncio
import os
from datetime import datetime
from hume import HumeClient
from hume.empathic_voice.types import PostedConfigPromptSpec, PostedUserDefinedToolSpec
import evi_config

async def create_fresh_config():
    """Create a fresh EVI config with tool enforcement."""
    
    client = HumeClient(api_key=os.getenv("HUME_API_KEY"))
    
    try:
        # Get our comprehensive config
        config_manager = evi_config.EVIConfigManager()
        config = config_manager.get_config_for_api_creation()
        hume_tools = config["tools"]
        
        print(f"🔧 Creating FRESH EVI config with mandatory tool usage...")
        print(f"   Tools: {len(hume_tools)}")
        print(f"   Prompt Length: {len(config['system_prompt'])} chars")
        print(f"🚨 Prompt enforces MANDATORY tool calling for settlements")
        
        # Create new config with minimal requirements
        new_config = await client.empathic_voice.configs.create(
            name=f"Portia Tool Enforced {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            prompt=PostedConfigPromptSpec(text=config["system_prompt"]),
            evi_version="3",
            tools=[PostedUserDefinedToolSpec(
                id=tool['name'],
                **tool
            ) for tool in hume_tools]
        )
        
        print(f"✅ SUCCESS: Created fresh config")
        print(f"   Config ID: {new_config.id}")
        print(f"   Name: {new_config.name}")
        
        # Update environment variable for main script
        with open(".env", "r") as f:
            env_content = f.read()
        
        # Update or add EVI_CONFIG_ID
        if "EVI_CONFIG_ID=" in env_content:
            # Replace existing
            lines = env_content.split('\n')
            new_lines = []
            for line in lines:
                if line.startswith("EVI_CONFIG_ID="):
                    new_lines.append(f"EVI_CONFIG_ID={new_config.id}")
                else:
                    new_lines.append(line)
            env_content = '\n'.join(new_lines)
        else:
            # Add new
            env_content += f"\nEVI_CONFIG_ID={new_config.id}\n"
        
        with open(".env", "w") as f:
            f.write(env_content)
        
        print(f"✅ Updated .env with new config ID")
        print(f"🚀 Now run: python main_evi.py")
        print(f"   The new config will enforce tool calling!")
        
        return new_config.id
        
    except Exception as e:
        print(f"❌ Failed to create fresh config: {e}")
        return None

if __name__ == "__main__":
    print("🎯 CREATING FRESH EVI CONFIG WITH TOOL ENFORCEMENT")
    print("This will force EVI to call tools when customers mention settlements")
    print("")
    
    config_id = asyncio.run(create_fresh_config())
    
    if config_id:
        print(f"\n🏁 SUCCESS! Fresh config created: {config_id}")
        print(f"Now when you say 'twenty-five thousand' EVI should call the tool!")
    else:
        print(f"\n❌ FAILED to create fresh config")
