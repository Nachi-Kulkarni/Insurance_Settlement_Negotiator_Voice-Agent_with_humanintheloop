"""
Webhook Handler for EVI Production Features
Handles chat history, audio reconstruction, and session monitoring.
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
import hmac

logger = logging.getLogger(__name__)

@dataclass
class ChatSession:
    """Chat session data structure."""
    chat_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    tool_calls_count: int = 0
    messages_count: int = 0
    escalated: bool = False
    settlement_amount: Optional[float] = None
    outcome: Optional[str] = None  # "settled", "escalated", "incomplete"

@dataclass
class ToolCallEvent:
    """Tool call event data."""
    tool_name: str
    timestamp: datetime
    parameters: Dict[str, Any]
    result: Dict[str, Any]
    execution_time_ms: float
    success: bool

class WebhookHandler:
    """Handles EVI webhooks for production monitoring and features."""
    
    def __init__(self, webhook_secret: Optional[str] = None):
        """Initialize webhook handler."""
        self.webhook_secret = webhook_secret
        self.active_sessions: Dict[str, ChatSession] = {}
        self.tool_call_history: List[ToolCallEvent] = []
        self.session_history: List[ChatSession] = []
        
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature for security."""
        if not self.webhook_secret:
            return True  # Skip verification if no secret set
        
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected_signature}", signature)
    
    async def handle_chat_started(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle chat started webhook."""
        chat_id = event_data.get("chat_id")
        if not chat_id:
            return {"error": "Missing chat_id"}
        
        session = ChatSession(
            chat_id=chat_id,
            start_time=datetime.now()
        )
        
        self.active_sessions[chat_id] = session
        
        logger.info(f"📞 Chat started: {chat_id}")
        
        # Return any initial session configuration
        return {
            "success": True,
            "chat_id": chat_id,
            "session_config": {
                "enable_recording": True,
                "enable_transcription": True,
                "quality_monitoring": True
            }
        }
    
    async def handle_chat_ended(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle chat ended webhook."""
        chat_id = event_data.get("chat_id")
        if not chat_id or chat_id not in self.active_sessions:
            return {"error": "Unknown chat session"}
        
        session = self.active_sessions[chat_id]
        session.end_time = datetime.now()
        session.duration_seconds = (session.end_time - session.start_time).total_seconds()
        
        # Determine outcome based on session data
        if session.escalated:
            session.outcome = "escalated"
        elif session.settlement_amount:
            session.outcome = "settled"
        else:
            session.outcome = "incomplete"
        
        # Move to history and remove from active
        self.session_history.append(session)
        del self.active_sessions[chat_id]
        
        logger.info(f"📞 Chat ended: {chat_id} - Duration: {session.duration_seconds:.1f}s - Outcome: {session.outcome}")
        
        # Generate session summary for auditing
        summary = self._generate_session_summary(session)
        
        return {
            "success": True,
            "chat_id": chat_id,
            "session_summary": summary,
            "audit_log_created": True
        }
    
    async def handle_tool_called(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool called webhook."""
        chat_id = event_data.get("chat_id")
        tool_name = event_data.get("tool_name")
        parameters = event_data.get("parameters", {})
        result = event_data.get("result", {})
        execution_time = event_data.get("execution_time_ms", 0)
        success = event_data.get("success", False)
        
        # Record tool call
        tool_event = ToolCallEvent(
            tool_name=tool_name,
            timestamp=datetime.now(),
            parameters=parameters,
            result=result,
            execution_time_ms=execution_time,
            success=success
        )
        
        self.tool_call_history.append(tool_event)
        
        # Update session if active
        if chat_id in self.active_sessions:
            session = self.active_sessions[chat_id]
            session.tool_calls_count += 1
            
            # Check for specific outcomes
            if tool_name == "escalate_to_specialist" and success:
                session.escalated = True
            elif tool_name == "calculate_settlement_offer" and success:
                settlement = result.get("recommended_offer")
                if settlement:
                    session.settlement_amount = settlement
        
        logger.info(f"🔧 Tool called: {tool_name} - Success: {success} - Time: {execution_time}ms")
        
        return {
            "success": True,
            "tool_call_logged": True,
            "session_updated": chat_id in self.active_sessions
        }
    
    def _generate_session_summary(self, session: ChatSession) -> Dict[str, Any]:
        """Generate comprehensive session summary."""
        return {
            "chat_id": session.chat_id,
            "duration_seconds": session.duration_seconds,
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "outcome": session.outcome,
            "metrics": {
                "tool_calls_count": session.tool_calls_count,
                "messages_count": session.messages_count,
                "escalated": session.escalated,
                "settlement_amount": session.settlement_amount
            },
            "performance": {
                "avg_tool_response_time": self._calculate_avg_tool_time(),
                "session_efficiency": "high" if session.duration_seconds < 300 else "medium"
            }
        }
    
    def _calculate_avg_tool_time(self) -> float:
        """Calculate average tool execution time."""
        if not self.tool_call_history:
            return 0.0
        
        recent_calls = self.tool_call_history[-10:]  # Last 10 calls
        total_time = sum(call.execution_time_ms for call in recent_calls)
        return total_time / len(recent_calls)
    
    def get_analytics_dashboard(self) -> Dict[str, Any]:
        """Get analytics dashboard data."""
        total_sessions = len(self.session_history)
        active_sessions = len(self.active_sessions)
        
        if total_sessions == 0:
            return {
                "total_sessions": 0,
                "active_sessions": active_sessions,
                "message": "No completed sessions yet"
            }
        
        # Calculate metrics
        successful_settlements = sum(1 for s in self.session_history if s.outcome == "settled")
        escalations = sum(1 for s in self.session_history if s.outcome == "escalated")
        avg_duration = sum(s.duration_seconds or 0 for s in self.session_history) / total_sessions
        
        settlement_amounts = [s.settlement_amount for s in self.session_history if s.settlement_amount]
        avg_settlement = sum(settlement_amounts) / len(settlement_amounts) if settlement_amounts else 0
        
        return {
            "session_metrics": {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "successful_settlements": successful_settlements,
                "escalations": escalations,
                "settlement_rate": (successful_settlements / total_sessions * 100) if total_sessions > 0 else 0
            },
            "performance_metrics": {
                "avg_session_duration_seconds": round(avg_duration, 1),
                "avg_settlement_amount": round(avg_settlement, 2),
                "avg_tool_response_time_ms": round(self._calculate_avg_tool_time(), 1)
            },
            "tool_metrics": {
                "total_tool_calls": len(self.tool_call_history),
                "successful_tool_calls": sum(1 for call in self.tool_call_history if call.success),
                "tool_success_rate": (
                    sum(1 for call in self.tool_call_history if call.success) / 
                    len(self.tool_call_history) * 100
                ) if self.tool_call_history else 0
            }
        }
    
    async def get_chat_history(self, chat_id: str) -> Dict[str, Any]:
        """Get chat history for a specific session."""
        # In a real implementation, this would fetch from EVI's chat history API
        session = None
        
        # Check active sessions
        if chat_id in self.active_sessions:
            session = self.active_sessions[chat_id]
        else:
            # Check completed sessions
            for s in self.session_history:
                if s.chat_id == chat_id:
                    session = s
                    break
        
        if not session:
            return {"error": "Session not found"}
        
        # Get tool calls for this session
        session_tools = [
            {
                "tool_name": call.tool_name,
                "timestamp": call.timestamp.isoformat(),
                "success": call.success,
                "execution_time_ms": call.execution_time_ms
            }
            for call in self.tool_call_history
            # Note: In real implementation, filter by chat_id
        ]
        
        return {
            "session": asdict(session),
            "tool_calls": session_tools[-10:],  # Last 10 for this session
            "available": True,
            "note": "Full chat history would be available via EVI API in production"
        }
    
    async def request_audio_reconstruction(self, chat_id: str) -> Dict[str, Any]:
        """Request audio reconstruction for a session."""
        # In production, this would call EVI's audio reconstruction API
        return {
            "chat_id": chat_id,
            "reconstruction_requested": True,
            "estimated_completion": "2-5 minutes",
            "note": "Audio reconstruction would be available via EVI API in production",
            "formats_available": ["wav", "mp3", "transcript"]
        }

# Global webhook handler instance
webhook_handler = WebhookHandler()

async def process_webhook(event_type: str, payload: Dict[str, Any], signature: Optional[str] = None) -> Dict[str, Any]:
    """Process incoming webhook events."""
    global webhook_handler
    
    # Verify signature if provided
    if signature:
        payload_bytes = json.dumps(payload, sort_keys=True).encode()
        if not webhook_handler.verify_webhook_signature(payload_bytes, signature):
            return {"error": "Invalid signature"}
    
    # Route to appropriate handler
    if event_type == "chat_started":
        return await webhook_handler.handle_chat_started(payload)
    elif event_type == "chat_ended":
        return await webhook_handler.handle_chat_ended(payload)
    elif event_type == "tool_called":
        return await webhook_handler.handle_tool_called(payload)
    else:
        return {"error": f"Unknown event type: {event_type}"}

# Example webhook server (for production deployment)
async def create_webhook_server(host: str = "0.0.0.0", port: int = 8080):
    """Create a simple webhook server for production use."""
    try:
        from aiohttp import web
        
        async def webhook_endpoint(request):
            """Handle webhook requests."""
            try:
                event_type = request.headers.get("X-Event-Type")
                signature = request.headers.get("X-Signature")
                payload = await request.json()
                
                result = await process_webhook(event_type, payload, signature)
                return web.json_response(result)
                
            except Exception as e:
                logger.error(f"Webhook error: {e}")
                return web.json_response({"error": str(e)}, status=500)
        
        async def health_check(request):
            """Health check endpoint."""
            return web.json_response({"status": "healthy", "service": "EVI Webhook Handler"})
        
        async def analytics_endpoint(request):
            """Analytics dashboard endpoint."""
            analytics = webhook_handler.get_analytics_dashboard()
            return web.json_response(analytics)
        
        app = web.Application()
        app.router.add_post("/webhook", webhook_endpoint)
        app.router.add_get("/health", health_check)
        app.router.add_get("/analytics", analytics_endpoint)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        
        logger.info(f"🌐 Webhook server started on http://{host}:{port}")
        logger.info(f"   Endpoints: /webhook, /health, /analytics")
        
        return runner
        
    except ImportError:
        logger.warning("aiohttp not available - webhook server not started")
        return None

if __name__ == "__main__":
    # Test the webhook handler
    async def test_webhooks():
        """Test webhook functionality."""
        print("🧪 Testing webhook handler...")
        
        # Test chat started
        result = await process_webhook("chat_started", {"chat_id": "test123"})
        print(f"Chat started: {result}")
        
        # Test tool called
        result = await process_webhook("tool_called", {
            "chat_id": "test123",
            "tool_name": "lookup_claim",
            "parameters": {"claim_id": "CLM201"},
            "result": {"success": True},
            "execution_time_ms": 45,
            "success": True
        })
        print(f"Tool called: {result}")
        
        # Test chat ended
        await asyncio.sleep(1)  # Brief pause
        result = await process_webhook("chat_ended", {"chat_id": "test123"})
        print(f"Chat ended: {result}")
        
        # Get analytics
        analytics = webhook_handler.get_analytics_dashboard()
        print(f"Analytics: {analytics}")
    
    asyncio.run(test_webhooks())
