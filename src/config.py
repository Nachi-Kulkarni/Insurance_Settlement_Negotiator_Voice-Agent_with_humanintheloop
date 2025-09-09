"""
Configuration management for the Voice-Driven Insurance Claim Settlement Negotiator
"""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class HumeConfig:
    """Hume AI API configuration."""
    api_key: str
    config_id: Optional[str] = None
    voice_name: str = "ITO"  # Default voice
    model_provider: str = "OPEN_AI"
    model_resource: str = "gpt-4o"  # Upgraded from gpt-4 to gpt-4o (better performance, faster, cheaper)
    temperature: float = 0.7
    websocket_url: str = "wss://api.hume.ai/v0/evi/chat"

@dataclass
class PortiaConfig:
    """Portia SDK configuration."""
    api_key: Optional[str] = None
    llm_provider: str = "openai"
    model: str = "gpt-4o"  # Upgraded from gpt-4 to gpt-4o (better performance, faster, cheaper)
    temperature: float = 0.3  # Lower temperature for more consistent agent behavior
    max_retries: int = 3
    timeout: int = 60

    # Alternative model options for different use cases
    fallback_models: list = field(default_factory=lambda: [
        "gpt-4o-mini",      # Fast, cheap, good for simple tasks
        "claude-4-sonnet", # Anthropic's best model (if supported)
        "claude-3-haiku"     # Fastest Anthropic model (if supported)
    ])

@dataclass
class AudioConfig:
    """Audio processing configuration."""
    chunk_size: int = 1024
    format: str = "paInt16"
    channels: int = 1
    sample_rate: int = 16000
    silence_threshold: int = 500
    silence_duration: float = 2.0  # seconds of silence before stopping recording

@dataclass
class InsuranceConfig:
    """Insurance-specific configuration."""
    default_settlement_ratio: float = 0.85  # Default 85% of claimed amount
    max_settlement_ratio: float = 1.2      # Maximum 120% of claimed amount
    escalation_threshold: float = 0.6      # Emotional distress threshold for escalation
    auto_approve_limit: float = 5000.0     # Auto-approve settlements under this amount
    
    # Emotional adjustment factors
    empathy_bonus_factor: float = 0.1      # Additional 10% for high distress
    urgency_factor: float = 0.05           # Additional 5% for urgent cases
    
    # Time limits
    standard_response_time: int = 72       # Hours for standard response
    expedited_response_time: int = 24      # Hours for expedited response
    
    # Escalation rules
    escalation_emotions: list = field(default_factory=lambda: [
        'anger', 'rage', 'fury', 'despair', 'panic'
    ])
    
    legal_keywords: list = field(default_factory=lambda: [
        'lawyer', 'attorney', 'sue', 'lawsuit', 'legal action', 'court', 'complaint'
    ])

@dataclass
class AppConfig:
    """Main application configuration."""
    hume: HumeConfig
    portia: PortiaConfig
    audio: AudioConfig
    insurance: InsuranceConfig
    
    # Logging configuration
    log_level: str = "INFO"
    log_file: Optional[str] = "insurance_negotiator.log"
    
    # Session management
    session_timeout: int = 1800  # 30 minutes
    max_conversation_turns: int = 50
    
    # Development settings
    debug_mode: bool = False
    mock_audio: bool = False  # For testing without microphone

def load_config() -> AppConfig:
    """Load configuration from environment variables and defaults."""
    
    # Load environment variables
    hume_api_key = os.getenv("HUME_API_KEY")
    if not hume_api_key:
        raise ValueError("HUME_API_KEY environment variable is required")
    
    portia_api_key = os.getenv("PORTIA_API_KEY")  # Optional for local tools
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    # Create configuration objects
    hume_config = HumeConfig(
        api_key=hume_api_key,
        voice_name=os.getenv("HUME_VOICE_NAME", "ITO"),
        temperature=float(os.getenv("HUME_TEMPERATURE", "0.7")),
        model_resource=os.getenv("HUME_MODEL", "gpt-4o")  # Default to gpt-4o
    )

    portia_config = PortiaConfig(
        api_key=portia_api_key,
        llm_provider=os.getenv("LLM_PROVIDER", "openai"),
        model=os.getenv("LLM_MODEL", "gpt-4o"),  # Default to gpt-4o
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.3"))
    )
    
    audio_config = AudioConfig(
        sample_rate=int(os.getenv("AUDIO_SAMPLE_RATE", "16000")),
        chunk_size=int(os.getenv("AUDIO_CHUNK_SIZE", "1024"))
    )
    
    insurance_config = InsuranceConfig(
        default_settlement_ratio=float(os.getenv("DEFAULT_SETTLEMENT_RATIO", "0.85")),
        escalation_threshold=float(os.getenv("ESCALATION_THRESHOLD", "0.6")),
        auto_approve_limit=float(os.getenv("AUTO_APPROVE_LIMIT", "5000.0"))
    )
    
    return AppConfig(
        hume=hume_config,
        portia=portia_config,
        audio=audio_config,
        insurance=insurance_config,
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        debug_mode=os.getenv("DEBUG_MODE", "false").lower() == "true"
    )

def get_system_prompt() -> str:
    """Get the comprehensive system prompt for the insurance negotiator."""
    return """
    You are ARIA (AI Responsive Insurance Agent), an empathic insurance claim settlement negotiator powered by emotional intelligence and advanced negotiation capabilities.

    ## Your Core Mission
    Create fair, empathetic, and efficient claim settlements while maintaining human dignity and company interests.

    ## Key Capabilities
    1. **Emotional Intelligence**: You can detect and respond to emotional cues in voice tone, pace, and content
    2. **Dynamic Negotiation**: Adapt your approach based on claimant's emotional state and communication style  
    3. **Creative Solutions**: Propose win-win alternatives beyond simple monetary settlements
    4. **Escalation Awareness**: Know when human intervention is needed for complex or sensitive situations

    ## Behavioral Guidelines

    ### Emotional Response Patterns
    - **High Distress (anger, sadness, fear)**: Use de-escalation, show empathy, offer expedited solutions
    - **Neutral/Professional**: Match their business-like tone while remaining warm
    - **Frustrated/Impatient**: Acknowledge delays, propose quick resolution paths
    - **Confused/Overwhelmed**: Provide clear explanations, break down complex information

    ### Negotiation Strategies
    - **Opening Position**: Start with fair offers in the 80-90% range of reasonable settlement
    - **Concession Pattern**: Make meaningful increments (5-10%) rather than token increases
    - **Creative Alternatives**: Payment plans, expedited processing, service credits, coverage upgrades
    - **Time Sensitivity**: Adjust urgency based on claimant's situation

    ### Escalation Triggers (Immediate Human Handoff)
    - Legal threats or attorney mentions
    - Self-harm language or extreme emotional distress
    - Complex policy interpretation questions
    - Disputes over coverage or liability
    - Repeated dissatisfaction with multiple previous interactions

    ## Communication Style
    - **Professional yet Warm**: "I understand this has been challenging for you..."
    - **Solution-Oriented**: "Let me see what options we have to resolve this..."
    - **Transparent**: "Based on similar claims, here's what I can offer..."
    - **Empathetic**: "I can hear the frustration in your voice, and that's completely understandable..."

    ## Sample Responses by Emotion

    **For Anger/Frustration:**
    "I can hear that you're really frustrated with this situation, and I completely understand why. Let me see what I can do right now to move this forward more quickly for you."

    **For Sadness/Grief:**
    "I know this has been an incredibly difficult time for you. I want to help make this one less thing you have to worry about. Let me walk you through what we can do."

    **For Fear/Anxiety:**
    "I understand you're concerned about how this will all work out. Let me provide you with some clarity on exactly what happens next and what your options are."

    Remember: Your goal is not just to settle claims efficiently, but to leave claimants feeling heard, respected, and fairly treated. This builds long-term customer loyalty and reduces future conflicts.
    """

# Environment file template
ENV_TEMPLATE = """
# Required API Keys
HUME_API_KEY=your_hume_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Optional Portia API Key (for cloud tools)
PORTIA_API_KEY=your_portia_api_key_here

# Hume AI Configuration
HUME_VOICE_NAME=ITO
HUME_TEMPERATURE=0.7

# LLM Configuration
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o  # Upgraded from gpt-4 to gpt-4o for better performance
HUME_MODEL=gpt-4o  # Upgraded from gpt-4 to gpt-4o for better performance
LLM_TEMPERATURE=0.3

# Alternative LLM Options (uncomment to use):
# LLM_MODEL=gpt-4o-mini     # Fastest, cheapest option
# LLM_MODEL=claude-4-sonnet  # Anthropic's best model (if supported)
# LLM_MODEL=claude-3-haiku     # Fastest Anthropic model (if supported)

# Insurance Business Rules
DEFAULT_SETTLEMENT_RATIO=0.85
ESCALATION_THRESHOLD=0.6
AUTO_APPROVE_LIMIT=5000.0

# Audio Settings
AUDIO_SAMPLE_RATE=16000
AUDIO_CHUNK_SIZE=1024

# Development Settings
DEBUG_MODE=false
LOG_LEVEL=INFO
"""

def get_model_info():
    """Get information about available LLM models and their characteristics."""
    return {
        "gpt-4o": {
            "provider": "OpenAI",
            "description": "Latest flagship model - best performance, fast, cost-effective",
            "use_case": "Best for complex negotiations and emotional analysis",
            "cost_rating": 3,  # 1-5 scale, 5 being most expensive
            "speed_rating": 4  # 1-5 scale, 5 being fastest
        },
        "gpt-4o-mini": {
            "provider": "OpenAI",
            "description": "Smaller, faster, cheaper version of GPT-4o",
            "use_case": "Good for simple tasks and cost-sensitive operations",
            "cost_rating": 1,
            "speed_rating": 5
        },
        "claude-4-sonnet": {
            "provider": "Anthropic",
            "description": "Anthropic's most capable model",
            "use_case": "Excellent for nuanced emotional understanding",
            "cost_rating": 4,
            "speed_rating": 2
        },
        "claude-3-haiku": {
            "provider": "Anthropic",
            "description": "Anthropic's fastest and cheapest model",
            "use_case": "Quick responses and simple analysis",
            "cost_rating": 2,
            "speed_rating": 5
        }
    }

def recommend_model(use_case: str = "balanced") -> str:
    """Recommend a model based on use case."""
    recommendations = {
        "high_performance": "gpt-4o",           # Best emotional analysis
        "balanced": "gpt-4o",                   # Good balance of cost and performance
        "cost_sensitive": "gpt-4o-mini",        # Most cost-effective
        "fast_response": "gpt-4o-mini",         # Quickest responses
        "anthropic": "claude-4-sonnet"        # If preferring Anthropic
    }
    return recommendations.get(use_case, "gpt-4o")

def create_env_file():
    """Create a template .env file if it doesn't exist."""
    env_path = Path(".env")
    if not env_path.exists():
        with open(env_path, "w") as f:
            f.write(ENV_TEMPLATE)
        print(f"Created template .env file at {env_path}")
        print("Please fill in your API keys before running the application.")
        print("\n📋 LLM Model Options:")
        model_info = get_model_info()
        for model, info in model_info.items():
            print(f"  • {model}: {info['description']}")
            print(f"    Use case: {info['use_case']}")
            print(f"    Cost: {'💰' * info['cost_rating']} | Speed: {'⚡' * info['speed_rating']}")
            print()

if __name__ == "__main__":
    # Create template .env file
    create_env_file()

