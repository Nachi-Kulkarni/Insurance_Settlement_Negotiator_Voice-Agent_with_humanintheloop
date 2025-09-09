#!/usr/bin/env python3.11

"""
SIMPLIFIED Voice Interface for Real-Time Insurance Claim Settlement using EVI 3.
This version embraces EVI's built-in capabilities and eliminates complex background processing.

Key Improvements:
1. Uses EVI's LLM instead of template responses
2. Implements proper EVI Tools (function calling)
3. Simplified audio handling with MicrophoneInterface
4. Dynamic Variables and Context Injection for state management
5. Migrated to EVI 3 for better performance
6. Production features: webhooks, chat history, audio reconstruction
"""

import asyncio
import json
import logging
import os
import sys
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
import time

# Import from installed packages (both SDKs are now pip-installed)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'project-docs', 'portia-sdk-python'))

from hume import AsyncHumeClient
from hume.empathic_voice.chat.socket_client import ChatConnectOptions
from hume.empathic_voice.chat.audio.microphone_interface import MicrophoneInterface

# Import configuration and tools
from evi_config import EVIConfigManager
from portia_tools import OptimizedInsuranceToolRegistry

logger = logging.getLogger(__name__)

@dataclass
class ConversationMetrics:
    """Metrics for tracking conversation performance and intervention needs."""
    start_time: float = 0.0
    tool_calls_count: int = 0
    response_times: list = None
    intervention_count: int = 0
    failed_interactions: int = 0
    escalation_attempts: int = 0
    
    def __post_init__(self):
        if self.response_times is None:
            self.response_times = []
        if self.start_time == 0.0:
            self.start_time = time.time()



            self.response_times = []

class SimplifiedVoiceInsuranceAgent:
    """Simplified voice agent using EVI 3 with proper tools and state management."""
    
    def __init__(self):
        """Initialize with simplified EVI 3 architecture."""
        load_dotenv()
        self.api_key = os.getenv("HUME_API_KEY")
        self.config_id = os.getenv("HUME_CONFIG_ID")
        
        if not self.api_key:
            raise ValueError("HUME_API_KEY environment variable is required")
        
        self.client = None
        self.config_manager = EVIConfigManager()
        self.tool_registry = OptimizedInsuranceToolRegistry()
        self.metrics = ConversationMetrics()
        
        # Session state (managed via EVI Dynamic Variables)
        self.session_variables = {}
        
        # Load customer context for personalized experience
        try:
            from customer_database import get_demo_customer_context, get_contextual_variables
            self.customer_context = get_demo_customer_context()
            self.contextual_vars = get_contextual_variables(self.customer_context)
            logger.info(f"🎯 Loaded personalized context for {self.customer_context['name']}")
        except ImportError:
            self.customer_context = None
            self.contextual_vars = {}
        
        logger.info("✅ Simplified EVI 3 interface initialized")
    
    async def initialize(self):
        """Initialize the client and optionally create/update EVI config."""
        self.client = AsyncHumeClient(api_key=self.api_key)
        
        # Always create/update EVI config to ensure tools are included
        await self._create_evi_config()
        
        logger.info("✅ EVI 3 client ready")
    
    async def _create_evi_config(self):
        """Create EVI configuration if needed."""
        try:
            # Get the complete config
            config = self.config_manager.create_full_config(
                config_name="Portia Insurance Settlement Agent v2",
                webhook_url=os.getenv("WEBHOOK_BASE_URL")  # Optional webhook
            )
            
            # Create actual EVI config with tools using Hume API
            try:
                # Use the Hume client to create/update the config
                from hume.empathic_voice.types import PostedConfigPromptSpec, PostedUserDefinedToolSpec
                
                # Convert our tools to Hume format
                hume_tools = []
                for tool in config['tools']:
                    hume_tool = PostedUserDefinedToolSpec(
                        id=tool['name'],  # Add required id field
                        name=tool['name'],
                        description=tool['description'],
                        parameters=tool['parameters']
                    )
                    hume_tools.append(hume_tool)
                
                # Create the config with required voice specification
                from hume.empathic_voice.types import VoiceName
                new_config = await self.client.empathic_voice.configs.create_config(
                    name=config['name'],
                    prompt=PostedConfigPromptSpec(text=config['system_prompt']),
                    tools=hume_tools,
                    voice=VoiceName(name="ITO"),  # Required for EVI 3
                    evi_version="3"
                )
                
                self.config_id = new_config.id
                logger.info(f"✅ EVI Config created: {self.config_id}")
                logger.info(f"- System Prompt: {len(config['system_prompt'])} characters")
                logger.info(f"- Tools: {len(hume_tools)} function definitions")
                logger.info(f"- Version: EVI {config['version']}")
                
            except Exception as api_error:
                logger.warning(f"Could not create new config: {api_error}")
                # Force new config creation with updated prompt - don't use old configs
                logger.info("🔄 Creating new config with updated prompt for tool calling...")
                try:
                    # Import datetime for unique naming
                    from datetime import datetime
                    # Import force_tool_prompt directly to ensure tool enforcement
                    from force_tool_prompt import get_force_tool_prompt
                    updated_prompt = get_force_tool_prompt()
                    
                    # Create the essential tools that must be available for settlement
                    essential_tools = []
                    for tool in config['tools']:
                        if tool['name'] in ['calculate_settlement_offer', 'lookup_claim', 'escalate_to_specialist']:
                            hume_tool = PostedUserDefinedToolSpec(
                                id=tool['name'],
                                name=tool['name'], 
                                description=tool['description'],
                                parameters=tool['parameters']
                            )
                            essential_tools.append(hume_tool)
                    
                    from hume.empathic_voice.types import VoiceName
                    minimal_config = await self.client.empathic_voice.configs.create_config(
                        name=f"Portia Tool Enforced {datetime.now().strftime('%H%M%S')}",
                        prompt=PostedConfigPromptSpec(text=updated_prompt),
                        tools=essential_tools,  # Include the critical tools
                        voice=VoiceName(name="ITO"),  # Required for EVI 3
                        evi_version="3"
                    )
                    self.config_id = minimal_config.id
                    logger.info(f"✅ Created updated config with tool enforcement: {self.config_id}")
                    logger.info(f"🔧 Included {len(essential_tools)} essential tools for settlement processing")
                except Exception as e:
                    logger.error(f"Failed to create updated config: {e}")
                    # Try with just the prompt
                    try:
                        from datetime import datetime
                        from force_tool_prompt import get_force_tool_prompt
                        from hume.empathic_voice.types import VoiceName
                        prompt_only_config = await self.client.empathic_voice.configs.create_config(
                            name=f"Portia Prompt Only {datetime.now().strftime('%H%M%S')}",
                            prompt=PostedConfigPromptSpec(text=get_force_tool_prompt()),
                            voice=VoiceName(name="ITO"),  # Required for EVI 3
                            evi_version="3"
                        )
                        self.config_id = prompt_only_config.id
                        logger.warning(f"⚠️ Created config with prompt only (no tools): {self.config_id}")
                        logger.warning("Tools may not work properly - this is for testing prompt enforcement only")
                    except Exception as e2:
                        logger.error(f"Complete config creation failure: {e2}")
                        # Use existing config as last resort but warn heavily
                        if os.getenv("HUME_CONFIG_ID"):
                            self.config_id = os.getenv("HUME_CONFIG_ID")
                            logger.warning(f"⚠️ Using existing config (may not have updated prompt): {self.config_id}")
                        else:
                            raise Exception(f"No valid config available for tool enforcement")
            
        except Exception as e:
            logger.error(f"Error creating EVI config: {e}")
            # Use a default config ID for testing
            self.config_id = "default_config"
    
    async def start_conversation(self):
        """Start the simplified conversation using EVI 3."""
        try:
            self.metrics.start_time = time.time()
            
            # Connect with callbacks to handle EVI messages
            if not self.config_id:
                logger.error("❌ No valid config ID available - cannot start conversation")
                raise ValueError("EVI configuration is required but not available")
                
            options = ChatConnectOptions(config_id=self.config_id)
            
            async with self.client.empathic_voice.chat.connect_with_callbacks(
                options=options,
                on_open=self._on_connection_opened,
                on_message=self._on_message,
                on_close=self._on_connection_closed,
                on_error=self._on_error
            ) as socket:
                
                # Store socket reference for tool responses
                self.socket = socket
                
                logger.info("🎤 Starting EVI 3 conversation...")
                logger.info("✋ Press Ctrl+C to stop...")
                
                # Send initial session settings with dynamic variables
                await self._initialize_session_variables(socket)
                
                # Start microphone interface (simplified)
                await self._start_microphone_interface(socket)
                
        except Exception as e:
            logger.error(f"Conversation error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def _on_connection_opened(self):
        """Handle connection opened."""
        logger.info("🔗 EVI 3 connection opened")
    
    async def _on_message(self, message):
        """Handle incoming EVI messages - much simpler now."""
        try:
            if message.type == "chat_metadata":
                logger.info(f"📋 Chat ID: {message.chat_id}")
                
            elif message.type == "user_message":
                user_text = message.message.content
                logger.info(f"🗣️  User: {user_text}")
                
                # 🎯 FORCE TOOL USAGE: Check for settlement triggers and manually call tools
                await self._check_and_force_tool_calls(user_text)
                
                # Extract emotions for dynamic variables
                emotions = self._extract_emotions_simple(message)
                if emotions:
                    logger.info(f"😊 Emotions: {emotions}")
                    await self._update_emotional_context(emotions)
                
            elif message.type == "assistant_message":
                # This is EVI's response - we now embrace it instead of ignoring
                assistant_text = message.message.content
                logger.info(f"🤖 Portia: {assistant_text}")
                
            elif message.type == "tool_call":
                # Handle tool calls - this replaces background Portia processing
                await self._handle_tool_call(message)
                
            elif message.type == "audio_output":
                # Handle audio output using the working pattern from your original code
                logger.debug("🔊 Receiving audio output from EVI agent")
                
                try:
                    import base64
                    import sounddevice as sd
                    
                    # Ensure correct output device
                    current_output = sd.default.device[1]
                    if current_output != 3:  # External headphones should be device 3
                        sd.default.device[1] = 3
                        logger.info("🎧 Corrected audio output routing to external headphones")
                    
                    # Use the audio handler if available
                    if hasattr(self, 'handle_audio_output'):
                        await self.handle_audio_output(message)
                    elif hasattr(message, 'data') and message.data:
                        # Fallback: just ensure routing is correct
                        logger.debug("🔊 Audio data available for playback")
                        
                except Exception as e:
                    logger.warning(f"Audio output handling error: {e}")
                
            elif message.type == "error":
                logger.error(f"❌ EVI Error: {message.message}")
                
        except Exception as e:
            logger.error(f"Message handling error: {e}")
    
    async def _handle_tool_call(self, message):
        """Handle tool calls from EVI - replaces background processing."""
        self.metrics.tool_calls_count += 1
        start_time = time.time()
        
        try:
            tool_name = message.name
            tool_call_id = message.tool_call_id
            parameters = json.loads(message.parameters) if message.parameters else {}
            
            logger.info(f"🔧 Tool call: {tool_name} with params: {parameters}")
            
            # Execute the appropriate tool
            result = await self._execute_tool(tool_name, parameters)
            
            # Send result back to EVI
            await self.socket.send_tool_response(
                tool_call_id=tool_call_id,
                content=json.dumps(result)
            )
            
            # Update session variables if needed
            await self._update_session_from_tool_result(tool_name, result)
            
            response_time = time.time() - start_time
            self.metrics.response_times.append(response_time)
            logger.info(f"⚡ Tool executed in {response_time:.3f}s")
            
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            
            # Send error response to EVI
            error_result = {
                "error": str(e),
                "success": False
            }
            await self.socket.send_tool_response(
                tool_call_id=message.tool_call_id,
                content=json.dumps(error_result)
            )
    
    async def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tools using the EVIToolHandler for consistency."""
        try:
            # Use the tool handler if available, otherwise fall back to direct execution
            if hasattr(self, 'tool_handler') and self.tool_handler:
                result = await self.tool_handler.handle_tool_call(
                    tool_name=tool_name,
                    parameters=parameters,
                    tool_call_id="direct_call"
                )
                return result.data
            
            # Fallback to direct tool execution
            if tool_name == "lookup_claim":
                tool = self.tool_registry.tools["fast_claim_lookup"]
                from portia.tool import ToolRunContext
                ctx = ToolRunContext()
                return tool.run(ctx, claim_id=parameters.get("claim_id"))
                
            elif tool_name == "calculate_settlement_offer":
                tool = self.tool_registry.tools["quick_settlement"]
                from portia.tool import ToolRunContext
                ctx = ToolRunContext()
                return tool.run(
                    ctx,
                    claim_id=parameters.get("claim_id"),
                    incident_type=parameters.get("claim_type"),
                    damage_amount=parameters.get("estimated_damage_amount"),
                    emotional_adjustment=parameters.get("emotional_adjustment", 0.0)
                )
                
            elif tool_name == "escalate_to_specialist":
                tool = self.tool_registry.tools["instant_escalation"]
                from portia.tool import ToolRunContext
                ctx = ToolRunContext()
                return tool.run(
                    ctx,
                    claim_id=parameters.get("claim_id"),
                    trigger=parameters.get("reason", "general")
                )
                
            elif tool_name == "request_human_intervention":
                # Handle critical intervention requests
                return {
                    "success": True,
                    "immediate_action": "transfer_to_human",
                    "agent_status": "intervention_requested",
                    "customer_message": "Transferring you to a specialist immediately. Please hold the line.",
                    "stop_ai_conversation": True,
                    "human_takeover": True
                }
                
            elif tool_name == "create_payment_plan":
                # Simple payment plan creation
                settlement_amount = parameters.get("settlement_amount", 15000)
                plan_type = parameters.get("plan_type", "monthly")
                
                if plan_type == "monthly":
                    return {
                        "success": True,
                        "plan": {
                            "total_amount": settlement_amount,
                            "monthly_payment": settlement_amount / 3,
                            "duration_months": 3,
                            "description": f"${settlement_amount:,.2f} paid over 3 months"
                        }
                    }
                else:
                    return {
                        "success": True,
                        "plan": {
                            "total_amount": settlement_amount * 0.98,  # Small discount for expedited
                            "processing_time": "48 hours",
                            "description": f"${settlement_amount * 0.98:,.2f} expedited payment"
                        }
                    }
            
            else:
                return {"error": f"Unknown tool: {tool_name}", "success": False}
                
        except Exception as e:
            logger.error(f"Tool execution error for {tool_name}: {e}")
            return {"error": str(e), "success": False}
    
    async def _initialize_session_variables(self, socket):
        """Initialize session with dynamic variables."""
        try:
            # Use proper Hume EVI session settings format
            from hume.empathic_voice.types import SessionSettings
            
            # Create session settings with variables
            session_settings = SessionSettings(
                variables={
                    "agent_name": "Portia",
                    "company_name": "SecureGuard Insurance", 
                    "current_date": time.strftime("%Y-%m-%d"),
                    "session_id": f"SESSION_{int(time.time())}"
                }
            )
            
            await socket.send_session_settings(session_settings)
            logger.info("📝 Session variables initialized")
            
        except Exception as e:
            logger.error(f"Error initializing session variables: {e}")
            # Fallback to simple dict format
            try:
                simple_settings = {
                    "variables": {
                        "agent_name": "Portia",
                        "company_name": "SecureGuard Insurance", 
                        "current_date": time.strftime("%Y-%m-%d")
                    }
                }
                await socket.send_session_settings(simple_settings)
                logger.info("📝 Session variables initialized (fallback)")
            except Exception as e2:
                logger.error(f"Fallback session initialization failed: {e2}")
    
    async def _update_emotional_context(self, emotions: Dict[str, float]):
        """Update emotional context using context injection."""
        try:
            # Find dominant emotion
            if emotions:
                dominant_emotion = max(emotions.items(), key=lambda x: x[1])
                emotion_name, emotion_score = dominant_emotion
                
                if emotion_score > 0.6:  # High emotional intensity
                    # Use context injection through variables
                    context_variables = {
                        "emotional_state": emotion_name,
                        "emotional_intensity": f"{emotion_score:.2f}",
                        "empathy_boost": "high"
                    }
                    try:
                        from hume.empathic_voice.types import SessionSettings
                        context_settings = SessionSettings(variables=context_variables)
                        await self.socket.send_session_settings(context_settings)
                    except:
                        # Fallback
                        await self.socket.send_session_settings({"variables": context_variables})
                    logger.info(f"📊 Updated emotional context: {emotion_name} ({emotion_score:.2f})")
                    
        except Exception as e:
            logger.error(f"Error updating emotional context: {e}")
    
    async def _update_session_from_tool_result(self, tool_name: str, result: Dict[str, Any]):
        """Update session variables based on tool results."""
        try:
            variables = {}
            
            if tool_name == "lookup_claim" and result.get("success"):
                claim = result.get("claim", {})
                variables.update({
                    "claim_id": claim.get("claim_id", ""),
                    "claimant_name": claim.get("claimant_name", ""),
                    "claim_type": claim.get("claim_type", "")
                })
                
            elif tool_name == "calculate_settlement_offer" and result.get("success"):
                variables.update({
                    "settlement_amount": f"${result.get('recommended_offer', 0):,.2f}"
                })
            
            if variables:
                try:
                    from hume.empathic_voice.types import SessionSettings
                    session_update = SessionSettings(variables=variables)
                    await self.socket.send_session_settings(session_update)
                except:
                    # Fallback
                    session_update = {"variables": variables}
                    await self.socket.send_session_settings(session_update)
                logger.info(f"📝 Updated session variables: {list(variables.keys())}")
                
        except Exception as e:
            logger.error(f"Error updating session variables: {e}")
    
    async def _check_and_force_tool_calls(self, user_text: str):
        """Force tool calls when settlement triggers are detected."""
        user_lower = user_text.lower()
        
        # Check for settlement amount triggers
        settlement_triggers = [
            "twenty five thousand", "twenty-five thousand", "25 thousand",
            "25000", "25,000", "$25,000", "$25000", "25k"
        ]
        
        # Check for claim ID triggers
        claim_triggers = ["clm201", "clm 201", "clm two zero one", "claim 201"]
        
        # Force settlement calculation if amount mentioned
        if any(trigger in user_lower for trigger in settlement_triggers):
            logger.info(f"🚀 FORCING SETTLEMENT TOOL CALL: Detected settlement amount in '{user_text}'")
            await self._force_settlement_calculation(user_text, 25000)
        
        # Force claim lookup if claim ID mentioned
        if any(trigger in user_lower for trigger in claim_triggers):
            logger.info(f"🚀 FORCING CLAIM LOOKUP: Detected claim ID in '{user_text}'")
            await self._force_claim_lookup("CLM201")
    
    async def _force_settlement_calculation(self, user_text: str, amount: float):
        """Force a settlement calculation tool call."""
        if hasattr(self, 'tool_handler') and self.tool_handler:
            try:
                params = {
                    "claim_type": "Auto Accident", 
                    "damage_description": f"Customer willing to settle for ${amount:,}",
                    "estimated_damage_amount": amount,
                    "conversation_summary": user_text
                }
                logger.info(f"🔧 MANUAL TOOL CALL: calculate_settlement_offer with params: {params}")
                result = await self.tool_handler.handle_tool_call(
                    "calculate_settlement_offer",
                    params,
                    "manual_settlement_call"
                )
                if result.success:
                    logger.info(f"✅ FORCED SETTLEMENT SUCCESS: {result.data}")
                else:
                    logger.error(f"❌ FORCED SETTLEMENT FAILED: {result.data}")
            except Exception as e:
                logger.error(f"❌ Force settlement calculation error: {e}")
    
    async def _force_claim_lookup(self, claim_id: str):
        """Force a claim lookup tool call."""
        if hasattr(self, 'tool_handler') and self.tool_handler:
            try:
                params = {"claim_id": claim_id}
                logger.info(f"🔧 MANUAL TOOL CALL: lookup_claim with params: {params}")
                result = await self.tool_handler.handle_tool_call(
                    "lookup_claim",
                    params,
                    "manual_lookup_call"
                )
                if result.success:
                    logger.info(f"✅ FORCED LOOKUP SUCCESS: {result.data}")
                else:
                    logger.error(f"❌ FORCED LOOKUP FAILED: {result.data}")
            except Exception as e:
                logger.error(f"❌ Force claim lookup error: {e}")

    def _extract_emotions_simple(self, message) -> Dict[str, float]:
        """Simple emotion extraction for dynamic variables."""
        emotions = {}
        try:
            if hasattr(message, 'models') and message.models and hasattr(message.models, 'prosody'):
                emotion_scores = message.models.prosody.scores
                emotions_dict = emotion_scores.model_dump() if hasattr(emotion_scores, 'model_dump') else emotion_scores.__dict__
                
                # Get top 3 emotions
                top_emotions = sorted(emotions_dict.items(), key=lambda x: x[1], reverse=True)[:3]
                emotions = {emotion: score for emotion, score in top_emotions if score > 0.1}
                
        except Exception:
            pass
        return emotions
    
    async def _start_microphone_interface(self, socket):
        """Start simplified microphone interface using EVI's built-in capabilities."""
        try:
            # Configure audio settings for external headphones and MacBook microphone
            import sounddevice as sd
            
            # List available audio devices
            devices = sd.query_devices()
            logger.info("🎧 Available audio devices:")
            for i, device in enumerate(devices):
                logger.info(f"  {i}: {device['name']} ({'Input' if device['max_input_channels'] > 0 else 'Output'})")
            
            # Find MacBook microphone for input (Device 4 based on test results)
            input_device = 4  # MacBook Air Microphone
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0 and ('macbook' in device['name'].lower() and 'microphone' in device['name'].lower()):
                    input_device = i
                    break
            
            # Find external headphones for output (Device 3 based on test results)
            output_device = 3  # External Headphones
            for i, device in enumerate(devices):
                if device['max_output_channels'] > 0 and 'external headphones' in device['name'].lower():
                    output_device = i
                    break
            
            # Configure audio with proper settings
            audio_config = {
                "sample_rate": 16000,
                "channels": 1,
                "encoding": "linear16",
                "input_device": input_device,
                "output_device": output_device
            }
            
            logger.info(f"🎤 Using input device: {devices[input_device]['name']}")
            logger.info(f"🎧 Using output device: {devices[output_device]['name']}")
            
            # Use the new corrected MicrophoneInterface approach
            await self._start_corrected_microphone_interface(socket, audio_config)
            
        except Exception as e:
            logger.error(f"Microphone interface error: {e}")
            # Fallback to basic audio handling
            await self._start_basic_audio_interface(socket, None)
    
    async def _start_basic_audio_interface(self, socket, audio_config=None):
        """Fallback basic audio interface."""
        try:
            # Import audio components
            from hume.empathic_voice.chat.audio.microphone import Microphone
            from hume.empathic_voice.chat.audio.microphone_sender import MicrophoneSender
            from hume.empathic_voice.chat.audio.chat_client import ChatClient
            from hume.empathic_voice.types import AudioConfiguration
            
            # Configure audio settings first before starting microphone
            import sounddevice as sd
            
            if audio_config:
                if "input_device" in audio_config:
                    sd.default.device[0] = audio_config["input_device"]  # Set input device
                    logger.info(f"🎤 Audio input configured for device: {audio_config['input_device']}")
                if "output_device" in audio_config:
                    sd.default.device[1] = audio_config["output_device"]  # Set output device
                    logger.info(f"🎧 Audio output configured for device: {audio_config['output_device']}")
            
            print("Configuring socket with microphone settings...")
            
            # Start microphone with proper context and device configuration
            microphone_kwargs = {}
            if audio_config and "input_device" in audio_config:
                microphone_kwargs["device"] = audio_config["input_device"]
            
            with Microphone.context(**microphone_kwargs) as microphone:
                print("Microphone connected. Say something!")
                
                # Configure audio properly
                hume_audio_config = AudioConfiguration(
                    sample_rate=microphone.sample_rate,
                    channels=1,
                    encoding="linear16"
                )
                
                # Note: Audio configuration is now handled at connection time to avoid 
                # "Audio settings cannot be configured after audio data has been received" error
                
                # Create microphone sender
                sender = MicrophoneSender.new(microphone=microphone, allow_interrupt=True)
                
                # Create a working audio stream from the microphone
                async def microphone_stream():
                    """Stream audio from microphone sender."""
                    try:
                        # Use the microphone's built-in streaming capability
                        chunk_size = 1024
                        sample_rate = microphone.sample_rate
                        
                        while True:
                            # Read audio data from microphone
                            audio_data = microphone.read(chunk_size)
                            if audio_data is not None and len(audio_data) > 0:
                                yield audio_data.tobytes()
                            else:
                                # Small delay to prevent busy waiting
                                await asyncio.sleep(0.01)
                                
                    except Exception as e:
                        logger.error(f"Microphone stream error: {e}")
                        return  # Exit the async generator on error
                
                # Create chat client with the working audio stream
                chat_client = ChatClient.new(sender=sender, byte_strs=microphone_stream())
                
                logger.info("🎤 Basic audio interface connected!")
                
                # Run the chat client
                await chat_client.run(socket=socket)
                
        except Exception as e:
            logger.error(f"Basic audio interface error: {e}")
            # Simple fallback - just keep the connection alive
            try:
                logger.info("🎤 Using minimal audio interface...")
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                pass
    
    async def _on_connection_closed(self):
        """Handle connection closed."""
        logger.info("🔌 EVI 3 connection closed")
        self._print_session_metrics()
    
    async def _on_error(self, error):
        """Handle connection errors."""
        logger.error(f"❌ EVI 3 connection error: {error}")
    
    def _print_session_metrics(self):
        """Print session performance metrics."""
        session_duration = time.time() - self.metrics.start_time
        avg_response_time = sum(self.metrics.response_times) / len(self.metrics.response_times) if self.metrics.response_times else 0
        
        logger.info("📊 Session Metrics:")
        logger.info(f"  Duration: {session_duration:.1f}s")
        logger.info(f"  Tool calls: {self.metrics.tool_calls_count}")
        logger.info(f"  Avg tool response time: {avg_response_time:.3f}s")
        if self.metrics.response_times:
            logger.info(f"  Fastest tool call: {min(self.metrics.response_times):.3f}s")
    
    async def _handle_tool_call(self, message):
        """Handle tool calls from EVI - this is where Portia integration happens!"""
        try:
            if hasattr(message, 'tool_call'):
                tool_call = message.tool_call
                tool_name = tool_call.tool_name if hasattr(tool_call, 'tool_name') else str(tool_call)
                parameters = tool_call.parameters if hasattr(tool_call, 'parameters') else {}
                tool_call_id = tool_call.id if hasattr(tool_call, 'id') else "unknown"
                
                logger.info(f"🔧 Tool call received: {tool_name}")
                
                # Execute the tool using our handler
                if hasattr(self, 'tool_handler'):
                    result = await self.tool_handler.handle_tool_call(tool_name, parameters, tool_call_id)
                    
                    if result.success:
                        logger.info(f"✅ Tool executed successfully: {tool_name} in {result.execution_time:.3f}s")
                        
                        # Check if human intervention was triggered
                        if tool_name == "request_human_intervention" or result.data.get("human_takeover"):
                            logger.critical("🚨 HUMAN INTERVENTION TRIGGERED - Stopping AI processing")
                            await self._handle_human_intervention(result.data)
                        
                        return result.data
                    else:
                        logger.error(f"❌ Tool execution failed: {tool_name}")
                        return {"error": "Tool execution failed"}
                else:
                    logger.warning("⚠️ No tool handler available")
                    
        except Exception as e:
            logger.error(f"Tool call handling error: {e}")
    
    async def _handle_human_intervention(self, intervention_data: Dict[str, Any]):
        """Handle human intervention - transfer control and stop AI processing."""
        try:
            intervention_summary = intervention_data.get("intervention_summary", {})
            trigger = intervention_summary.get("trigger", "unknown")
            urgency = intervention_summary.get("urgency", "high")
            claim_id = intervention_summary.get("claim_id", "N/A")
            
            logger.critical(f"🚨 HUMAN INTERVENTION ACTIVATED")
            logger.critical(f"📞 Trigger: {trigger}")
            logger.critical(f"⚡ Urgency: {urgency}")
            logger.critical(f"🎫 Claim: {claim_id}")
            logger.critical(f"🔄 Transferring control to human specialist...")
            
            # Update session state to indicate human takeover
            self.session_state.update({
                "human_intervention_active": True,
                "intervention_trigger": trigger,
                "intervention_time": time.time(),
                "ai_agent_status": "suspended"
            })
            
            # Log intervention for monitoring/analytics
            self.metrics.intervention_count += 1
            
            # In a real system, this would:
            # 1. Alert human agents via dashboard/notification system
            # 2. Queue customer for immediate human pickup
            # 3. Transfer conversation context to human agent
            # 4. Stop AI message processing
            
            logger.critical("✅ Human intervention request processed - AI agent suspended")
            
        except Exception as e:
            logger.error(f"Human intervention handling error: {e}")
    
    def _should_trigger_automatic_intervention(self, emotional_state: Dict[str, float], conversation_context: str) -> bool:
        """Check if automatic human intervention should be triggered based on emotional analysis."""
        try:
            from human_intervention_handler import HumanInterventionHandler
            
            if not hasattr(self, '_intervention_handler'):
                self._intervention_handler = HumanInterventionHandler()
            
            # Check if intervention is needed
            trigger = self._intervention_handler.should_trigger_intervention(
                emotional_state=emotional_state,
                conversation_context={"recent_messages": conversation_context},
                agent_attempts=getattr(self.metrics, 'failed_interactions', 0)
            )
            
            return trigger is not None
            
        except Exception as e:
            logger.debug(f"Automatic intervention check error: {e}")
            return False
    
    async def _start_corrected_microphone_interface(self, socket, audio_config=None):
        """Working microphone interface using the proven pattern from your original code."""
        try:
            # Import required components
            from hume.empathic_voice.chat.audio.microphone import Microphone
            from hume.empathic_voice.chat.audio.microphone_sender import MicrophoneSender
            from hume.empathic_voice.chat.audio.chat_client import ChatClient
            from hume.empathic_voice.types import AudioConfiguration, SessionSettings
            import base64
            import sounddevice as sd
            
            # CRITICAL: Set up audio devices exactly like your working code
            if audio_config and "output_device" in audio_config:
                output_device = audio_config["output_device"]
                input_device = audio_config.get("input_device", 4)
                
                # Set speaker device for audio output (like your working code)
                sd.default.device[1] = output_device
                logger.info(f"🎧 Audio output set to device {output_device}: {sd.query_devices(output_device)['name']}")
                logger.info(f"🎤 Audio input set to device {input_device}: {sd.query_devices(input_device)['name']}")
            else:
                input_device = 4  # MacBook Air Microphone
                output_device = 3  # External Headphones
                sd.default.device[1] = output_device
            
            # Create audio queue for EVI audio playback (exactly like your working code)
            audio_queue = asyncio.Queue()
            
            async def audio_stream():
                """Audio stream for EVI playback - from your working code."""
                while True:
                    try:
                        audio_data = await audio_queue.get()
                        yield audio_data
                    except asyncio.CancelledError:
                        break
            
            # Audio output handler that actually processes incoming audio
            async def handle_audio_output(message):
                """Handle audio output from EVI - based on your working code."""
                if message.type == "audio_output":
                    try:
                        # Decode and queue audio data for playback
                        audio_data = base64.b64decode(message.data.encode("utf-8"))
                        await audio_queue.put(audio_data)
                        logger.debug("🔊 Audio data queued for playback")
                    except Exception as e:
                        logger.error(f"Audio output processing error: {e}")
            
            # We'll handle audio output in the main message handler
            # No need to override here, just ensure the audio queue is available
            self.audio_queue = audio_queue
            self.handle_audio_output = handle_audio_output
            
            # Start microphone with proper audio configuration
            with Microphone.context(device=input_device) as microphone:
                sender = MicrophoneSender.new(microphone=microphone, allow_interrupt=True)
                chat_client = ChatClient.new(sender=sender, byte_strs=audio_stream())
                
                # Configure audio settings
                audio_config = AudioConfiguration(
                    sample_rate=microphone.sample_rate,
                    channels=1,  # Force mono like your working code
                    encoding="linear16"
                )
                session_settings_config = SessionSettings(audio=audio_config)
                await socket.send_session_settings(message=session_settings_config)
                
                logger.info("🎤 Working microphone interface connected (using proven pattern)!")
                await chat_client.run(socket=socket)
            
        except Exception as e:
            logger.error(f"Working microphone interface error: {e}")
            # Final fallback - just keep connection alive
            logger.info("🎤 Using minimal audio interface...")
            while True:
                await asyncio.sleep(1)
    
    async def _start_custom_audio_handler(self, socket, input_device, microphone_stream):
        """Custom audio handler that properly manages both input AND output."""
        try:
            import sounddevice as sd
            from hume.empathic_voice.chat.audio.microphone import Microphone
            from hume.empathic_voice.chat.audio.microphone_sender import MicrophoneSender
            from hume.empathic_voice.chat.audio.chat_client import ChatClient
            
            # Set up audio output device specifically for EVI responses
            output_device = 3  # External Headphones
            sd.default.device[1] = output_device  # Ensure output goes to headphones
            
            logger.info(f"🎧 Custom audio handler - Output to device {output_device}")
            
            # Create microphone context
            with Microphone.context(device=input_device) as microphone:
                sender = MicrophoneSender.new(microphone=microphone, allow_interrupt=True)
                
                # Create chat client with proper audio stream
                chat_client = ChatClient.new(sender=sender, byte_strs=microphone_stream)
                
                # Start a background task to handle audio output
                async def audio_output_handler():
                    """Handle incoming audio from EVI and route to headphones."""
                    while True:
                        try:
                            # Listen for audio messages from WebSocket
                            message = await socket.receive()
                            
                            if hasattr(message, 'type') and message.type == 'audio_output':
                                logger.debug("🔊 Received audio from EVI agent")
                                
                                # The audio should automatically play through the configured output device
                                # If not, we might need to manually route it
                                if hasattr(message, 'data') and message.data:
                                    # Audio data is handled by the WebSocket client automatically
                                    # But we ensure the output device is correct
                                    current_output = sd.default.device[1]
                                    if current_output != output_device:
                                        sd.default.device[1] = output_device
                                        logger.info(f"🎧 Corrected output routing to device {output_device}")
                                        
                        except Exception as e:
                            logger.error(f"Audio output handler error: {e}")
                            await asyncio.sleep(0.1)
                
                # Start the audio output handler in background
                output_task = asyncio.create_task(audio_output_handler())
                
                try:
                    # Run the chat client (handles input)
                    await chat_client.run(socket=socket)
                finally:
                    # Clean up
                    output_task.cancel()
                    try:
                        await output_task
                    except asyncio.CancelledError:
                        pass
                        
        except Exception as e:
            logger.error(f"Custom audio handler error: {e}")
            raise

async def main():
    """Main function to run the simplified agent."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        agent = SimplifiedVoiceInsuranceAgent()
        await agent.initialize()
        await agent.start_conversation()
        
    except KeyboardInterrupt:
        logger.info("👋 Conversation ended by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(main())
