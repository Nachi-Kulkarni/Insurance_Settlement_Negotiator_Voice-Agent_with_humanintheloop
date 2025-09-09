"""
Human-in-the-Loop Intervention Handler for Extreme Customer Situations
Handles situations where AI agent cannot cope with uncontrollable customers.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import time

from portia.clarification import (
    CustomClarification, 
    UserVerificationClarification,
    ClarificationCategory
)
from portia.clarification_handler import ClarificationHandler
from portia.tool import Tool, ToolRunContext
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class InterventionTrigger(Enum):
    """Types of triggers that require human intervention."""
    EXTREME_ANGER = "extreme_anger"
    UNCONTROLLABLE_BEHAVIOR = "uncontrollable_behavior"
    LEGAL_THREATS = "legal_threats"
    ABUSIVE_LANGUAGE = "abusive_language"
    SUICIDE_IDEATION = "suicide_ideation"
    REPEATED_ESCALATION_FAILURE = "repeated_escalation_failure"
    COMPLEX_LEGAL_CASE = "complex_legal_case"
    HIGH_VALUE_DISPUTE = "high_value_dispute"
    REGULATORY_COMPLIANCE = "regulatory_compliance"
    AGENT_FAILURE = "agent_failure"

class InterventionUrgency(Enum):
    """Urgency levels for human intervention."""
    IMMEDIATE = "immediate"      # < 30 seconds
    HIGH = "high"               # < 2 minutes  
    MEDIUM = "medium"           # < 5 minutes
    STANDARD = "standard"       # < 15 minutes

@dataclass
class InterventionContext:
    """Context information for human intervention."""
    trigger: InterventionTrigger
    urgency: InterventionUrgency
    conversation_summary: str
    emotional_state: Dict[str, float]
    claim_id: Optional[str]
    customer_history: Dict[str, Any]
    agent_attempts: List[str]
    failure_reason: str
    handoff_notes: str

class HumanInterventionArgs(BaseModel):
    """Arguments for human intervention tool."""
    trigger: str = Field(..., description="Type of intervention trigger")
    urgency_level: str = Field(..., description="Urgency level (immediate, high, medium, standard)")
    conversation_summary: str = Field(..., description="Summary of conversation leading to intervention")
    emotional_state: Dict[str, float] = Field(default_factory=dict, description="Customer emotional state")
    claim_id: Optional[str] = Field(None, description="Associated claim ID if available")
    failure_reason: str = Field(..., description="Why the agent cannot handle this situation")
    customer_threats: Optional[str] = Field(None, description="Any threats or concerning statements")
    attempted_solutions: List[str] = Field(default_factory=list, description="Solutions already attempted")

class HumanInterventionTool(Tool):
    """Tool to trigger human intervention for uncontrollable situations."""
    
    id: str = "request_human_intervention"
    name: str = "Request Human Intervention"
    description: str = """
    CRITICAL TOOL: Use this when the customer is completely uncontrollable, extremely angry, 
    threatening legal action, using abusive language, or when the AI agent has failed multiple times.
    This immediately transfers control to a human specialist and stops AI intervention.
    """
    args_schema: type[BaseModel] = HumanInterventionArgs
    output_schema: tuple[str, str] = ("dict", "Human intervention details and next steps")
    
    def run(
        self, 
        ctx: ToolRunContext, 
        trigger: str,
        urgency_level: str,
        conversation_summary: str,
        emotional_state: Dict[str, float] = None,
        claim_id: Optional[str] = None,
        failure_reason: str = "",
        customer_threats: Optional[str] = None,
        attempted_solutions: List[str] = None
    ) -> Dict[str, Any]:
        """Execute human intervention process."""
        
        emotional_state = emotional_state or {}
        attempted_solutions = attempted_solutions or []
        
        # Validate trigger
        try:
            intervention_trigger = InterventionTrigger(trigger)
        except ValueError:
            intervention_trigger = InterventionTrigger.AGENT_FAILURE
        
        # Determine urgency
        try:
            urgency = InterventionUrgency(urgency_level)
        except ValueError:
            urgency = InterventionUrgency.HIGH  # Default to high for safety
        
        # Create intervention context
        context = InterventionContext(
            trigger=intervention_trigger,
            urgency=urgency,
            conversation_summary=conversation_summary,
            emotional_state=emotional_state,
            claim_id=claim_id,
            customer_history=self._get_customer_history(claim_id),
            agent_attempts=attempted_solutions,
            failure_reason=failure_reason,
            handoff_notes=self._generate_handoff_notes(
                intervention_trigger, conversation_summary, customer_threats
            )
        )
        
        # Log critical intervention
        logger.critical(f"🚨 HUMAN INTERVENTION REQUESTED: {trigger} - {urgency.value.upper()}")
        logger.critical(f"📞 Claim: {claim_id}, Reason: {failure_reason}")
        
        # Generate appropriate response based on trigger
        response = self._generate_intervention_response(context)
        
        # Create clarification for human handoff
        clarification = self._create_handoff_clarification(context)
        
        return {
            "success": True,
            "intervention_triggered": True,
            "urgency": urgency.value,
            "trigger": trigger,
            "handoff_message": response["agent_message"],
            "human_briefing": response["human_briefing"],
            "estimated_response_time": response["response_time"],
            "clarification": clarification,
            "stop_ai_processing": True,
            "transfer_control": "human_specialist",
            "context": {
                "conversation_summary": conversation_summary,
                "emotional_state": emotional_state,
                "claim_id": claim_id,
                "customer_threats": customer_threats,
                "attempted_solutions": attempted_solutions
            }
        }
    
    def _get_customer_history(self, claim_id: Optional[str]) -> Dict[str, Any]:
        """Get customer interaction history."""
        if not claim_id:
            return {"history": "No claim ID available"}
        
        # In a real system, this would query customer database
        return {
            "previous_calls": 0,
            "escalation_history": [],
            "satisfaction_score": "unknown",
            "risk_level": "high"  # Default to high when intervention needed
        }
    
    def _generate_handoff_notes(
        self, 
        trigger: InterventionTrigger, 
        summary: str, 
        threats: Optional[str]
    ) -> str:
        """Generate comprehensive handoff notes for human agent."""
        
        notes = f"**INTERVENTION TRIGGER**: {trigger.value.replace('_', ' ').title()}\n\n"
        notes += f"**CONVERSATION SUMMARY**: {summary}\n\n"
        
        if threats:
            notes += f"**⚠️ CUSTOMER THREATS/CONCERNS**: {threats}\n\n"
        
        notes += "**RECOMMENDED APPROACH**:\n"
        
        if trigger == InterventionTrigger.EXTREME_ANGER:
            notes += "- Use extreme de-escalation techniques\n"
            notes += "- Acknowledge frustration immediately\n"
            notes += "- Offer immediate senior management involvement\n"
            notes += "- Consider expedited settlement with management authorization\n"
            
        elif trigger == InterventionTrigger.LEGAL_THREATS:
            notes += "- Document all legal threats precisely\n"
            notes += "- Engage legal department immediately\n"
            notes += "- Do NOT make any admissions of liability\n"
            notes += "- Follow legal escalation protocol\n"
            
        elif trigger == InterventionTrigger.ABUSIVE_LANGUAGE:
            notes += "- Set professional boundaries immediately\n"
            notes += "- Document abusive language for records\n"
            notes += "- Warn customer about professional conduct expectations\n"
            notes += "- Be prepared to terminate call if abuse continues\n"
            
        elif trigger == InterventionTrigger.SUICIDE_IDEATION:
            notes += "- **CRITICAL**: Follow suicide prevention protocol\n"
            notes += "- Do NOT hang up under any circumstances\n"
            notes += "- Connect to mental health resources\n"
            notes += "- Alert supervisor and legal team immediately\n"
            
        else:
            notes += "- Assess situation carefully before proceeding\n"
            notes += "- Use senior agent de-escalation training\n"
            notes += "- Consider management involvement\n"
        
        return notes
    
    def _generate_intervention_response(self, context: InterventionContext) -> Dict[str, Any]:
        """Generate appropriate response for customer and human briefing."""
        
        trigger = context.trigger
        urgency = context.urgency
        
        # Agent message to customer
        if trigger == InterventionTrigger.LEGAL_THREATS:
            agent_message = """
            I understand you're considering legal action, and I want to make sure you get the proper attention this deserves. 
            I'm immediately transferring you to our senior specialist who handles these types of situations. 
            They have additional authority and will be with you within the next 60 seconds. 
            Please hold the line - this is being prioritized at the highest level.
            """
            response_time = "< 60 seconds"
            
        elif trigger == InterventionTrigger.EXTREME_ANGER:
            agent_message = """
            I can hear how extremely frustrated you are, and I completely understand why you're feeling this way. 
            This situation clearly needs immediate attention from someone with more authority than I have. 
            I'm connecting you right now to our senior resolution specialist who can take immediate action on your case. 
            Please stay on the line - they'll be with you in just a moment.
            """
            response_time = "< 30 seconds"
            
        elif trigger == InterventionTrigger.ABUSIVE_LANGUAGE:
            agent_message = """
            I want to help resolve your situation, but I need to connect you with a senior specialist 
            who is better equipped to handle complex cases like yours. They have additional resources 
            and authority that I don't have access to. Please hold while I transfer you immediately.
            """
            response_time = "< 2 minutes"
            
        else:
            agent_message = """
            I want to make sure you get the best possible service, and I believe this situation 
            would be better handled by one of our senior specialists. They have additional training 
            and authority to resolve complex situations like yours. I'm transferring you now - 
            please hold the line and they'll be right with you.
            """
            response_time = "< 5 minutes"
        
        # Human briefing
        emotional_summary = ", ".join([f"{k}:{v:.1f}" for k, v in context.emotional_state.items()])
        
        human_briefing = f"""
        **URGENT HUMAN INTERVENTION REQUIRED**
        
        **Customer State**: {trigger.value.replace('_', ' ').title()}
        **Urgency**: {urgency.value.upper()}
        **Claim ID**: {context.claim_id or 'Not provided'}
        **Emotional State**: {emotional_summary or 'High distress detected'}
        
        **Situation Summary**:
        {context.conversation_summary}
        
        **Why AI Failed**:
        {context.failure_reason}
        
        **Handoff Notes**:
        {context.handoff_notes}
        
        **Immediate Actions Required**:
        1. Connect within {response_time}
        2. Review full conversation history
        3. Apply appropriate de-escalation protocol
        4. Consider management escalation if needed
        """
        
        return {
            "agent_message": agent_message.strip(),
            "human_briefing": human_briefing.strip(),
            "response_time": response_time
        }
    
    def _create_handoff_clarification(self, context: InterventionContext) -> Dict[str, Any]:
        """Create a clarification for human handoff process."""
        
        return {
            "type": "CustomClarification",
            "id": f"human_intervention_{int(time.time())}",
            "title": f"Human Intervention Required - {context.trigger.value.title()}",
            "description": context.handoff_notes,
            "urgency": context.urgency.value,
            "claim_id": context.claim_id,
            "customer_context": {
                "emotional_state": context.emotional_state,
                "conversation_summary": context.conversation_summary,
                "failure_reason": context.failure_reason
            }
        }

class HumanInterventionHandler:
    """Handler for managing human intervention workflows."""
    
    def __init__(self):
        self.active_interventions: Dict[str, InterventionContext] = {}
        self.intervention_stats = {
            "total_interventions": 0,
            "by_trigger": {},
            "average_response_time": 0.0,
            "success_rate": 0.0
        }
    
    async def trigger_intervention(
        self, 
        trigger: InterventionTrigger,
        conversation_summary: str,
        emotional_state: Dict[str, float],
        claim_id: Optional[str] = None,
        customer_threats: Optional[str] = None,
        agent_failure_reason: str = "AI agent unable to proceed"
    ) -> Dict[str, Any]:
        """Trigger human intervention with appropriate urgency."""
        
        # Determine urgency based on trigger
        urgency_mapping = {
            InterventionTrigger.SUICIDE_IDEATION: InterventionUrgency.IMMEDIATE,
            InterventionTrigger.EXTREME_ANGER: InterventionUrgency.IMMEDIATE,
            InterventionTrigger.LEGAL_THREATS: InterventionUrgency.HIGH,
            InterventionTrigger.ABUSIVE_LANGUAGE: InterventionUrgency.HIGH,
            InterventionTrigger.UNCONTROLLABLE_BEHAVIOR: InterventionUrgency.HIGH,
            InterventionTrigger.HIGH_VALUE_DISPUTE: InterventionUrgency.MEDIUM,
            InterventionTrigger.COMPLEX_LEGAL_CASE: InterventionUrgency.MEDIUM,
            InterventionTrigger.REGULATORY_COMPLIANCE: InterventionUrgency.MEDIUM,
        }
        
        urgency = urgency_mapping.get(trigger, InterventionUrgency.STANDARD)
        
        # Create intervention tool
        tool = HumanInterventionTool()
        
        # Create minimal context for tool execution
        from portia import Config
        import os
        config = Config(
            llm_provider="openai",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            default_model="gpt-4o"
        )
        ctx = ToolRunContext(
            end_user={"external_id": "intervention_user", "id": "user_intervention_123"},
            plan_run={"id": "run_intervention_123", "plan_id": "plan_intervention_123", "end_user_id": "user_intervention_123"},
            plan={"id": "plan_intervention_123", "plan_context": {}, "steps": []},
            config=config,
            clarifications=[]
        )
        
        # Execute intervention
        result = tool.run(
            ctx=ctx,
            trigger=trigger.value,
            urgency_level=urgency.value,
            conversation_summary=conversation_summary,
            emotional_state=emotional_state,
            claim_id=claim_id,
            failure_reason=agent_failure_reason,
            customer_threats=customer_threats,
            attempted_solutions=[]
        )
        
        # Track intervention
        self.intervention_stats["total_interventions"] += 1
        trigger_count = self.intervention_stats["by_trigger"].get(trigger.value, 0)
        self.intervention_stats["by_trigger"][trigger.value] = trigger_count + 1
        
        logger.critical(f"🚨 Human intervention triggered: {trigger.value} (Urgency: {urgency.value})")
        
        return result
    
    def should_trigger_intervention(
        self, 
        emotional_state: Dict[str, float],
        conversation_context: Dict[str, Any],
        agent_attempts: int = 0
    ) -> Optional[InterventionTrigger]:
        """Determine if human intervention should be triggered based on context."""
        
        # Check emotional thresholds
        anger = emotional_state.get("anger", 0.0)
        distress = emotional_state.get("distress", 0.0)
        frustration = emotional_state.get("frustration", 0.0)
        
        # Extreme emotional states
        if anger > 0.9 or distress > 0.9:
            return InterventionTrigger.EXTREME_ANGER
        
        # Combined high emotions
        if anger > 0.8 and frustration > 0.8:
            return InterventionTrigger.UNCONTROLLABLE_BEHAVIOR
        
        # Check conversation context
        conversation_text = conversation_context.get("recent_messages", "").lower()
        
        # Legal threat detection
        legal_keywords = ["lawyer", "attorney", "sue", "lawsuit", "legal action", "court"]
        if any(keyword in conversation_text for keyword in legal_keywords):
            return InterventionTrigger.LEGAL_THREATS
        
        # Abusive language detection
        abusive_keywords = ["stupid", "idiot", "useless", "hate", "terrible"]
        if any(keyword in conversation_text for keyword in abusive_keywords):
            return InterventionTrigger.ABUSIVE_LANGUAGE
        
        # Agent failure detection
        if agent_attempts > 3:
            return InterventionTrigger.REPEATED_ESCALATION_FAILURE
        
        return None

# Export the intervention components
__all__ = [
    "HumanInterventionTool", 
    "HumanInterventionHandler", 
    "InterventionTrigger",
    "InterventionUrgency"
]
