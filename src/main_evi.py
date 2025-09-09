#!/usr/bin/env python3.11

"""
Production-Ready EVI 3 Insurance Claim Settlement System
Main entry point that brings together all the simplified components.

This replaces the complex voice_interface.py with a clean, production-ready system.
"""

import asyncio
import logging
import os
import sys
from typing import Optional
from dotenv import load_dotenv

# Import simplified components
from voice_interface_simplified import SimplifiedVoiceInsuranceAgent
from evi_tool_handler import EVIToolHandler
from evi_config import EVIConfigManager, create_evi_config_json

# Optional Portia integration
try:
    from portia import Portia
    PORTIA_AVAILABLE = True
except ImportError:
    PORTIA_AVAILABLE = False
    Portia = None

def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """Setup comprehensive logging."""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        handlers=handlers
    )
    
    # Set specific loggers
    logging.getLogger("hume").setLevel(logging.WARNING)  # Reduce Hume SDK noise
    logging.getLogger("websockets").setLevel(logging.WARNING)  # Reduce websocket noise

def check_environment() -> bool:
    """Check if all required environment variables are set."""
    required_vars = ["HUME_API_KEY", "OPENAI_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these in your .env file or environment.")
        return False
    
    return True

def print_startup_info():
    """Print system information at startup."""
    print("\n" + "="*60)
    print("🏛️  PORTIA - Insurance Claim Settlement Agent")
    print("    Powered by Hume EVI 3 & Advanced AI")
    print("="*60)
    print(f"🔧 EVI Version: 3 (Latest)")
    print(f"🤖 LLM Model: GPT-4o (Optimized)")
    print(f"📊 Tools: {len(EVIConfigManager().tools)} Available")
    print(f"🎤 Audio: High-Quality Voice Interface")
    print(f"⚡ Performance: Sub-500ms Response Times")
    if PORTIA_AVAILABLE:
        print(f"🧠 Advanced Analysis: Portia SDK Available")
    print("="*60)

async def initialize_portia() -> Optional[Portia]:
    """Initialize Portia instance if available and configured."""
    if not PORTIA_AVAILABLE:
        print("ℹ️  Portia SDK not available - using optimized tools only")
        return None
    
    try:
        portia_api_key = os.getenv("PORTIA_API_KEY")
        if not portia_api_key:
            print("ℹ️  PORTIA_API_KEY not set - using local tools only")
            return None
        
        # Initialize Portia with optimized settings for dashboard integration
        from portia import Config, StorageClass
        config = Config(
            llm_provider="openai",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            default_model="gpt-4o",
            storage_class=StorageClass.CLOUD,  # Enable dashboard integration
            portia_api_key=portia_api_key
        )
        portia_instance = Portia(config=config)
        
        print("✅ Portia SDK initialized for advanced analysis")
        return portia_instance
        
    except Exception as e:
        print(f"⚠️  Could not initialize Portia SDK: {e}")
        print("   Continuing with local tools only...")
        return None

async def run_conversation_loop(agent: SimplifiedVoiceInsuranceAgent):
    """Run the main conversation loop with error recovery."""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            print(f"\n🎤 Starting conversation (attempt {retry_count + 1}/{max_retries})...")
            await agent.start_conversation()
            break  # Success - exit retry loop
            
        except KeyboardInterrupt:
            print("\n👋 Conversation ended by user")
            break
            
        except Exception as e:
            retry_count += 1
            print(f"❌ Conversation error: {e}")
            
            if retry_count < max_retries:
                print(f"🔄 Retrying in 3 seconds... ({retry_count}/{max_retries})")
                await asyncio.sleep(3)
            else:
                print("❌ Max retries reached. Please check your configuration.")
                raise

async def main():
    """Main function - production entry point."""
    # Load environment
    load_dotenv()
    
    # Setup logging
    setup_logging(
        level=os.getenv("LOG_LEVEL", "INFO"),
        log_file=os.getenv("LOG_FILE")
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Print startup information
        print_startup_info()
        
        # Check environment
        if not check_environment():
            return 1
        
        # Initialize Portia (optional)
        portia_instance = await initialize_portia()
        
        # Create and initialize the simplified agent
        print("\n🚀 Initializing EVI 3 agent...")
        agent = SimplifiedVoiceInsuranceAgent()
        await agent.initialize()
        
        # Show personalized context if available
        if hasattr(agent, 'customer_context') and agent.customer_context:
            print(f"\n🎯 PERSONALIZED DEMO MODE:")
            print(f"   Customer: {agent.customer_context['name']}")
            print(f"   Active Claim: {agent.contextual_vars.get('claim_id', 'Unknown')}")
            print(f"   Incident: {agent.contextual_vars.get('incident_type', 'Unknown')}")
            print(f"   Days Pending: {agent.contextual_vars.get('days_since_incident', 0)}")
            print(f"   Expected Settlement: ${agent.contextual_vars.get('recommended_settlement', 0):,}")
            print(f"   Customer Satisfaction: {agent.contextual_vars.get('customer_satisfaction', 0)}/5")
            print("   💡 Try saying: 'Hi, this is Nachiket calling about CLM201'")
        else:
            print("   📝 Using generic configuration")
        
        # Initialize tool handler with Portia if available
        tool_handler = EVIToolHandler(portia_instance)
        print(f"🔧 Tool handler initialized with {len(tool_handler.tool_registry.get_tools())} tools")
        
        # Connect tool handler to the agent - THIS IS CRITICAL!
        agent.tool_handler = tool_handler
        print("🔗 Tool handler connected to EVI agent")
        
        # Print final status
        print("\n✅ System ready!")
        print("💬 You can now speak to Portia for insurance claim settlement")
        print("🛑 Press Ctrl+C to stop the conversation\n")
        
        # Run conversation with error recovery
        await run_conversation_loop(agent)
        
        # Print final statistics
        if hasattr(agent, 'metrics'):
            agent._print_session_metrics()
        
        stats = tool_handler.get_performance_stats()
        if stats["total_tool_calls"] > 0:
            print("\n📊 Tool Performance Statistics:")
            print(f"   Total calls: {stats['total_tool_calls']}")
            print(f"   Success rate: {stats['success_rate_percent']}%")
            print(f"   Avg response: {stats['average_execution_time_ms']}ms")
        
        return 0
        
    except Exception as e:
        logger.error(f"System error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return 1

def create_env_template():
    """Create a template .env file for easy setup."""
    env_content = """# Hume AI Configuration
HUME_API_KEY=your_hume_api_key_here
HUME_CONFIG_ID=your_config_id_here

# OpenAI Configuration (required for LLM)
OPENAI_API_KEY=your_openai_api_key_here

# Portia SDK Configuration (optional - for advanced analysis)
PORTIA_API_KEY=your_portia_api_key_here

# Optional Configuration
LOG_LEVEL=INFO
LOG_FILE=insurance_agent.log
WEBHOOK_BASE_URL=https://your-webhook-url.com

# Model Configuration
LLM_MODEL=gpt-4o
LLM_TEMPERATURE=0.7
"""
    
    with open(".env.template", "w") as f:
        f.write(env_content)
    
    print("📝 Created .env.template file")
    print("   Copy this to .env and fill in your API keys")

def show_config_example():
    """Show an example EVI configuration."""
    print("\n📋 Example EVI Configuration:")
    config = create_evi_config_json("production")
    print(config[:500] + "..." if len(config) > 500 else config)

if __name__ == "__main__":
    import sys
    
    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--create-env":
            create_env_template()
            sys.exit(0)
        elif sys.argv[1] == "--show-config":
            show_config_example()
            sys.exit(0)
        elif sys.argv[1] == "--help":
            print("🏛️  Portia Insurance Claim Settlement Agent")
            print("\nUsage:")
            print("  python main_evi.py                 # Run the agent")
            print("  python main_evi.py --create-env    # Create .env template")
            print("  python main_evi.py --show-config   # Show EVI config example")
            print("  python main_evi.py --help          # Show this help")
            sys.exit(0)
    
    # Run the main application
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
        sys.exit(0)
