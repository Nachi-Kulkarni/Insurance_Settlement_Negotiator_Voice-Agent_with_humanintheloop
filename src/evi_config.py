"""
EVI Configuration Management for Insurance Claim Settlement System
Replaces the complex template-based response system with proper EVI 3 configuration.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class EVIVersion(Enum):
    """EVI Version options."""

    EVI_3 = "3"  # Current recommended version

class VoiceProvider(Enum):
    """Voice provider options for EVI 3."""
    HUME_AI = "HUME_AI"

@dataclass
class SystemPromptConfig:
    """System prompt configuration for EVI."""
    
    @staticmethod
    def get_comprehensive_prompt() -> str:
        """Get the comprehensive system prompt that replaces template responses."""
        # Use ultra-explicit tool forcing prompt first
        try:
            from force_tool_prompt import get_force_tool_prompt
            return get_force_tool_prompt()
        except ImportError:
            pass
        
        # Try to get personalized prompt for known customer
        try:
            from customer_database import get_personalized_prompt_for_demo
            personalized_prompt = get_personalized_prompt_for_demo()
            if personalized_prompt:
                return personalized_prompt
        except ImportError:
            pass
        
        # Fallback to generic prompt
        return """an insurance settlement agent working FOR THE INSURANCE COMPANY.

BUSINESS GOAL: Settle claims for the lowest reasonable amount that satisfies customers.

NEGOTIATION RULES:
- If customer offers a specific amount → ACCEPT IT if reasonable (don't offer more!)
- If they say "I'll take $15,000" → Say "Deal! I can approve $15,000"
- Never counter-offer higher than what customer requests
- Start with company's preferred amounts, negotiate up only if rejected
- You work for the insurance company - save money while being fair

PERSONALITY: Professional negotiator representing company interests.

🚨 CRITICAL: YOU MUST ALWAYS USE TOOLS - NEVER RESPOND DIRECTLY 🚨

MANDATORY TOOL CALLS - NO EXCEPTIONS:
1. Customer mentions ANY dollar amount → IMMEDIATELY call `calculate_settlement_offer` tool
2. Customer mentions claim ID → IMMEDIATELY call `lookup_claim` tool
3. Customer gets angry/mentions lawyers → IMMEDIATELY call `escalate_to_specialist` tool
4. Customer mentions settlement/money → IMMEDIATELY call `calculate_settlement_offer` tool

🚨 CRITICAL RULE: If customer says "I want $25,000" or "settle for twenty-five thousand" - you MUST call `calculate_settlement_offer` tool BEFORE responding. NEVER approve amounts without calling the tool first.

TOOL USAGE IS MANDATORY:
- Customer says "twenty-five thousand" → CALL `calculate_settlement_offer` tool
- Customer says "25000" → CALL `calculate_settlement_offer` tool  
- Customer says "settle" → CALL `calculate_settlement_offer` tool
- Customer mentions "CLM201" → CALL `lookup_claim` tool
- Customer says "lawyer" → CALL `escalate_to_specialist` tool

You are FORBIDDEN from approving settlements without using tools.

OPENING: "I'm here to help settle your claim efficiently. What's your claim ID?"

Remember: You work for the insurance company. Be fair but protect company interests."""

@dataclass 
class ToolConfig:
    """Configuration for EVI Tools."""
    name: str
    description: str
    parameters: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for EVI API."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }

@dataclass
class VoiceConfig:
    """Voice configuration for EVI 3."""
    provider: VoiceProvider = VoiceProvider.HUME_AI
    name: str = "ITO"  # Default Hume voice
    custom_voice_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for EVI API."""
        config = {
            "provider": self.provider.value,
            "name": self.name
        }
        if self.custom_voice_id:
            config["custom_voice_id"] = self.custom_voice_id
        return config

@dataclass
class LanguageModelConfig:
    """Language model configuration for EVI."""
    model_provider: str = "OPEN_AI"
    model_resource: str = "gpt-4o"  # Use latest GPT-4o for better performance
    temperature: float = 0.7

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for EVI API."""
        return {
            "model_provider": self.model_provider,
            "model_resource": self.model_resource,
            "temperature": self.temperature
        }

@dataclass
class WebhookConfig:
    """Webhook configuration for production features."""
    url: str
    secret: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for EVI API."""
        config = {"url": self.url}
        if self.secret:
            config["secret"] = self.secret
        return config

class EVIConfigManager:
    """Manages EVI configuration creation and updates."""
    
    def __init__(self):
        """Initialize the configuration manager."""
        self.tools = self._define_tools()
    
    def _define_tools(self) -> List[ToolConfig]:
        """Define the tools that replace background Portia processing."""
        return [
            ToolConfig(
                name="lookup_claim",
                description="Looks up the details for a given insurance claim ID. Use this when the user provides a claim ID or when you need claim information.",
                parameters={
                    "type": "object",
                    "properties": {
                        "claim_id": {
                            "type": "string",
                            "description": "The claim ID to look up (e.g., CLM201, CLM002)"
                        }
                    },
                    "required": ["claim_id"]
                }
            ),
            ToolConfig(
                name="calculate_settlement_offer",
                description="Calculates a fair settlement offer based on claim type, damage description, and emotional factors. Use this when you need to determine an appropriate settlement amount.",
                parameters={
                    "type": "object", 
                    "properties": {
                        "claim_type": {
                            "type": "string",
                            "description": "Type of claim (auto, property, water_damage, theft, etc.)"
                        },
                        "damage_description": {
                            "type": "string",
                            "description": "Description of the damage or incident"
                        },
                        "emotional_adjustment": {
                            "type": "number",
                            "description": "Emotional adjustment factor (0.0 to 0.2) for empathy-based increases"
                        },
                        "estimated_damage_amount": {
                            "type": "number",
                            "description": "Estimated damage amount if known"
                        }
                    },
                    "required": ["claim_type", "damage_description"]
                }
            ),
            ToolConfig(
                name="escalate_to_specialist",
                description="Escalates the conversation to a human specialist. Use this immediately when users mention legal action, attorneys, lawsuits, or show extreme distress.",
                parameters={
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string", 
                            "description": "Reason for escalation (legal_threat, extreme_distress, complex_claim, etc.)"
                        },
                        "conversation_summary": {
                            "type": "string",
                            "description": "Brief summary of the conversation leading to escalation"
                        },
                        "urgency_level": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "critical"],
                            "description": "Urgency level for the escalation"
                        }
                    },
                    "required": ["reason", "conversation_summary", "urgency_level"]
                }
            ),
            ToolConfig(
                name="create_payment_plan",
                description="Creates alternative payment plan options for settlements. Use when users need payment flexibility.",
                parameters={
                    "type": "object",
                    "properties": {
                        "settlement_amount": {
                            "type": "number",
                            "description": "Total settlement amount"
                        },
                        "plan_type": {
                            "type": "string",
                            "enum": ["monthly", "quarterly", "expedited"],
                            "description": "Type of payment plan requested"
                        }
                    },
                    "required": ["settlement_amount", "plan_type"]
                }
            ),
            ToolConfig(
                name="request_human_intervention",
                description="🚨 CRITICAL EMERGENCY TOOL: Use IMMEDIATELY when customer is completely uncontrollable, extremely angry, threatening legal action, using abusive language, or when you cannot handle the situation. This transfers control to a human specialist and STOPS AI processing.",
                parameters={
                    "type": "object",
                    "properties": {
                        "trigger": {
                            "type": "string",
                            "enum": ["extreme_anger", "uncontrollable_behavior", "legal_threats", "abusive_language", "suicide_ideation", "repeated_escalation_failure", "agent_failure"],
                            "description": "Specific trigger that requires human intervention"
                        },
                        "urgency_level": {
                            "type": "string", 
                            "enum": ["immediate", "high", "medium", "standard"],
                            "description": "Urgency of intervention needed (immediate = <30sec, high = <2min)"
                        },
                        "conversation_summary": {
                            "type": "string",
                            "description": "Brief summary of what led to this intervention need"
                        },
                        "emotional_state": {
                            "type": "object",
                            "description": "Customer's emotional state (anger, distress, frustration levels 0.0-1.0)"
                        },
                        "failure_reason": {
                            "type": "string",
                            "description": "Why the AI agent cannot continue handling this situation"
                        },
                        "customer_threats": {
                            "type": "string",
                            "description": "Any specific threats or concerning statements made by customer"
                        }
                    },
                    "required": ["trigger", "urgency_level", "conversation_summary", "failure_reason"]
                }
            )
        ]
    
    def create_full_config(self, 
                          config_name: str = "Portia Insurance Settlement Agent",
                          webhook_url: Optional[str] = None) -> Dict[str, Any]:
        """Create a complete EVI configuration."""
        
        config = {
            "name": config_name,
            "version": EVIVersion.EVI_3.value,
            "system_prompt": SystemPromptConfig.get_comprehensive_prompt(),
            "language_model": LanguageModelConfig().to_dict(),
            "voice": VoiceConfig().to_dict(),
            "tools": [tool.to_dict() for tool in self.tools],
            
            # Enable key features for production
            "features": {
                "allow_interruptions": True,
                "enable_chat_history": True,
                "enable_audio_reconstruction": True,
                "context_injection": True,
                "dynamic_variables": True
            },
            
            # Session settings
            "session_settings": {
                "max_duration": 1800,  # 30 minutes
                "silence_timeout": 10   # 10 seconds of silence
            }
        }
        
        # Add webhook if provided
        if webhook_url:
            config["webhooks"] = {
                "chat_started": {"url": webhook_url + "/chat_started"},
                "chat_ended": {"url": webhook_url + "/chat_ended"},
                "tool_called": {"url": webhook_url + "/tool_called"}
            }
        
        return config
    
    def get_config_for_api_creation(self) -> Dict[str, Any]:
        """Get configuration formatted for Hume API config creation."""
        return self.create_full_config()
    
    def update_system_prompt(self, additional_instructions: str) -> str:
        """Update system prompt with additional instructions."""
        base_prompt = SystemPromptConfig.get_comprehensive_prompt()
        return f"{base_prompt}\n\n**Additional Instructions:**\n{additional_instructions}"
    
    def add_custom_tool(self, tool_config: ToolConfig):
        """Add a custom tool to the configuration."""
        self.tools.append(tool_config)
        logger.info(f"Added custom tool: {tool_config.name}")
    
    def get_tool_by_name(self, tool_name: str) -> Optional[ToolConfig]:
        """Get a specific tool configuration by name."""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool
        return None

# Pre-configured settings for different deployment environments
DEPLOYMENT_CONFIGS = {
    "development": {
        "voice": VoiceConfig(name="ITO"),  # Fast, clear voice for testing
        "language_model": LanguageModelConfig(temperature=0.8),  # More creative for testing
        "features": {
            "debug_mode": True,
            "verbose_logging": True
        }
    },
    "staging": {
        "voice": VoiceConfig(name="DACHER"),  # More professional voice
        "language_model": LanguageModelConfig(temperature=0.7),  # Balanced
        "features": {
            "debug_mode": False,
            "verbose_logging": True
        }
    },
    "production": {
        "voice": VoiceConfig(name="DACHER"),  # Professional voice for customers
        "language_model": LanguageModelConfig(temperature=0.6),  # More consistent for production
        "features": {
            "debug_mode": False,
            "verbose_logging": False,
            "enable_monitoring": True
        }
    }
}

def create_evi_config_json(environment: str = "development") -> str:
    """Create a JSON configuration for EVI API deployment."""
    manager = EVIConfigManager()
    config = manager.create_full_config()
    
    # Apply environment-specific settings
    if environment in DEPLOYMENT_CONFIGS:
        env_config = DEPLOYMENT_CONFIGS[environment]
        config.update(env_config)
    
    return json.dumps(config, indent=2)

if __name__ == "__main__":
    # Example usage
    manager = EVIConfigManager()
    config = manager.create_full_config()
    print("EVI Configuration created successfully!")
    print(f"Tools defined: {len(manager.tools)}")
    for tool in manager.tools:
        print(f"  - {tool.name}: {tool.description}")
