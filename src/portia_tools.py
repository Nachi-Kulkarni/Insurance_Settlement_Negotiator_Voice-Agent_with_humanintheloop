"""
Lightweight Portia tool implementations optimized for real-time usage.
These tools prioritize speed over comprehensive analysis.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from portia import Tool, ToolRegistry
from portia.tool import ToolRunContext
from pydantic import BaseModel, Field
import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Lightweight argument models
class FastClaimLookupArgs(BaseModel):
    claim_id: Optional[str] = Field(None, description="Claim ID to lookup (optional)")

class QuickSettlementArgs(BaseModel):
    claim_id: Optional[str] = Field(None, description="Claim ID for settlement calculation (optional)")
    incident_type: Optional[str] = Field(None, description="Type of incident (auto, property, water damage)")
    damage_amount: Optional[float] = Field(None, description="Estimated damage amount")
    emotional_adjustment: Optional[float] = Field(0.0, description="Emotional adjustment factor (0.0-0.2)")

class InstantEscalationArgs(BaseModel):
    claim_id: Optional[str] = Field(None, description="Claim ID needing escalation (optional)")
    trigger: str = Field(..., description="Escalation trigger (legal, distress, etc.)")

# In-memory claim database for instant access
CLAIMS_DB = {
    "CLM201": {
        "claim_id": "CLM201",
        "policy_number": "POL_NK_2024",
        "claimant_name": "Nachiket Kulkarni",
        "incident_date": "2024-08-15",
        "claim_type": "Auto Accident",
        "estimated_damage": 15750,
        "status": "Settlement Pending",
        "settlement_range": {"min": 12000, "max": 18000, "recommended": 14500},
        "previous_offers": [],
        "priority": "high",  # Due to customer satisfaction history and time sensitivity
        "incident_details": {
            "location": "Highway 101, San Francisco",
            "fault_assessment": "Other party 80% at fault",
            "damage_description": "Rear-end collision, moderate damage to front bumper and hood",
            "injuries": "Minor whiplash, cleared by medical"
        },
        "customer_context": {
            "satisfaction_history": 4.8,
            "days_pending": 9,
            "previous_interactions": 3,
            "urgency_reason": "business trip next week",
            "communication_style": "direct_professional"
        }
    },
    "CLM002": {
        "claim_id": "CLM002",
        "policy_number": "POL789012", 
        "claimant_name": "Sarah Johnson",
        "incident_date": "2024-08-10",
        "claim_type": "Water Damage",
        "estimated_damage": 8500,
        "status": "Pending Documentation",
        "settlement_range": {"min": 6000, "max": 10000, "recommended": 7500},
        "previous_offers": [{"amount": 5500, "date": "2024-08-20", "status": "rejected"}],
        "priority": "standard"
    },
    "CLM003": {
        "claim_id": "CLM003",
        "policy_number": "POL555666",
        "claimant_name": "Michael Davis",
        "incident_date": "2024-08-20",
        "claim_type": "Property Damage",
        "estimated_damage": 25000,
        "status": "Complex Review",
        "settlement_range": {"min": 20000, "max": 30000, "recommended": 22500},
        "previous_offers": [],
        "priority": "high"
    }
}

class FastClaimLookupTool(Tool):
    """Ultra-fast claim lookup with in-memory database."""
    
    id: str = "fast_claim_lookup"
    name: str = "Fast Claim Lookup"
    description: str = "Instant claim lookup from memory cache"
    args_schema: type[BaseModel] = FastClaimLookupArgs
    output_schema: tuple[str, str] = ("dict", "Claim details or error")
    
    def run(self, ctx: ToolRunContext, claim_id: Optional[str] = None) -> Dict[str, Any]:
        """Lightning-fast claim lookup."""
        if not claim_id:
            return {
                "success": False,
                "message": "No claim ID provided - proceeding with general consultation",
                "available_claims": list(CLAIMS_DB.keys()),
                "general_info": "We can still help with general settlement guidance"
            }
        
        claim_id = claim_id.upper()
        if claim_id in CLAIMS_DB:
            claim_data = CLAIMS_DB[claim_id].copy()
            logger.info(f"⚡ Found claim {claim_id} in {0.001:.3f}s")
            return {
                "success": True,
                "claim": claim_data,
                "lookup_time": "instant"
            }
        
        return {
            "error": f"Claim {claim_id} not found",
            "available_claims": list(CLAIMS_DB.keys())
        }

class QuickSettlementTool(Tool):
    """Ultra-fast settlement calculation with pre-computed ranges."""
    
    id: str = "quick_settlement"
    name: str = "Quick Settlement Calculator"
    description: str = "Instant settlement calculation with emotional adjustments"
    args_schema: type[BaseModel] = QuickSettlementArgs
    output_schema: tuple[str, str] = ("dict", "Settlement offer with alternatives")
    
    def run(self, ctx: ToolRunContext, claim_id: Optional[str] = None, incident_type: Optional[str] = None, damage_amount: Optional[float] = None, emotional_adjustment: Optional[float] = 0.0) -> Dict[str, Any]:
        """Calculate settlement offer instantly."""
        # Handle case where no claim_id is provided - generate general settlement
        if not claim_id:
            # Generate general settlement based on incident type and damage
            incident_type = incident_type or "general incident"
            damage_amount = damage_amount or 10000  # Default estimate
            
            # General settlement calculations
            base_offer = damage_amount * 0.75  # 75% of damage as base
            settlement_range = {
                "min": damage_amount * 0.6,
                "max": damage_amount * 0.9, 
                "recommended": base_offer
            }
        else:
            claim_id = claim_id.upper()
            if claim_id not in CLAIMS_DB:
                return {"error": f"Claim {claim_id} not found"}
            
            claim = CLAIMS_DB[claim_id]
            base_offer = claim["settlement_range"]["recommended"]
            settlement_range = claim["settlement_range"]
        
        # Apply emotional adjustment (0-20% increase)
        emotional_adjustment = max(0.0, min(0.2, emotional_adjustment or 0.0))
        adjusted_offer = base_offer * (1 + emotional_adjustment)
        
        # Ensure within settlement range
        max_offer = settlement_range["max"]
        final_offer = min(adjusted_offer, max_offer)
        
        # Generate instant alternatives
        alternatives = {
            "payment_plan": {
                "amount": final_offer * 0.95,
                "terms": "3 monthly payments",
                "description": f"${final_offer * 0.95:,.2f} in 3 monthly installments"
            },
            "expedited": {
                "amount": final_offer * 0.98,
                "terms": "48-hour processing",
                "description": f"${final_offer * 0.98:,.2f} with expedited 48-hour processing"
            },
            "full_settlement": {
                "amount": final_offer,
                "terms": "standard processing",
                "description": f"${final_offer:,.2f} with standard 5-business-day processing"
            }
        }
        
        logger.info(f"⚡ Calculated settlement for {claim_id}: ${final_offer:,.2f}")
        
        return {
            "success": True,
            "claim_id": claim_id,
            "recommended_offer": final_offer,
            "base_amount": base_offer,
            "emotional_adjustment": emotional_adjustment,
            "alternatives": alternatives,
            "reasoning": f"Based on {incident_type or (claim.get('claim_type', 'general incident') if claim_id else 'general incident')}" + 
                        (f" with ${damage_amount or (claim.get('estimated_damage', 10000) if claim_id else 10000):,} damage" if damage_amount or claim_id else "") + 
                        (f" + {emotional_adjustment*100:.0f}% emotional consideration" if emotional_adjustment > 0 else ""),
            "calculation_time": "instant"
        }

class InstantEscalationTool(Tool):
    """Instant escalation detection and routing."""
    
    id: str = "instant_escalation"
    name: str = "Instant Escalation"
    description: str = "Immediate escalation processing for urgent cases"
    args_schema: type[BaseModel] = InstantEscalationArgs
    output_schema: tuple[str, str] = ("dict", "Escalation details")
    
    def run(self, ctx: ToolRunContext, claim_id: Optional[str] = None, trigger: str = "general") -> Dict[str, Any]:
        """Process escalation immediately."""
        escalation_id = f"ESC{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Determine urgency and routing
        urgency_map = {
            "legal": {"level": "high", "department": "Legal Affairs", "sla": "1 hour"},
            "distress": {"level": "high", "department": "Senior Support", "sla": "30 minutes"},
            "complex": {"level": "medium", "department": "Specialist Team", "sla": "2 hours"},
            "complaint": {"level": "medium", "department": "Customer Relations", "sla": "4 hours"}
        }
        
        escalation_info = urgency_map.get(trigger, {
            "level": "medium", 
            "department": "General Support", 
            "sla": "4 hours"
        })
        
        escalation_record = {
            "escalation_id": escalation_id,
            "claim_id": claim_id.upper() if claim_id else "GENERAL",
            "trigger": trigger,
            "urgency": escalation_info["level"],
            "assigned_department": escalation_info["department"],
            "sla": escalation_info["sla"],
            "created_at": datetime.datetime.now().isoformat(),
            "status": "created",
            "auto_generated": True
        }
        
        logger.info(f"⚡ Created escalation {escalation_id} for {claim_id} - {trigger}")
        
        # In a real system, this would be sent to escalation queue
        
        return {
            "success": True,
            "escalation": escalation_record,
            "next_steps": f"Case escalated to {escalation_info['department']}. Response expected within {escalation_info['sla']}.",
            "user_message": self._get_escalation_message(trigger),
            "processing_time": "instant"
        }
    
    def _get_escalation_message(self, trigger: str) -> str:
        """Get appropriate message for escalation type."""
        messages = {
            "legal": "I understand you're considering legal action. I'm immediately connecting you with our legal specialists who can address your concerns properly.",
            "distress": "I can hear how upset you are about this situation. Let me get a senior specialist involved right now to ensure we resolve this appropriately.",
            "complex": "This situation requires specialized attention. I'm routing your case to our expert team who can provide the detailed review it deserves.",
            "complaint": "I want to make sure your concerns are properly addressed. I'm escalating this to our customer relations team for immediate attention."
        }
        return messages.get(trigger, "Your case has been escalated for specialized attention.")

class LightweightAnalyticsArgs(BaseModel):
    claim_id: Optional[str] = Field(None, description="Optional claim ID for specific analytics")

class LightweightAnalyticsTool(Tool):
    """Lightweight analytics for conversation insights."""
    
    id: str = "quick_analytics"
    name: str = "Quick Analytics"
    description: str = "Fast conversation and claim analytics"
    args_schema: type[BaseModel] = LightweightAnalyticsArgs
    output_schema: tuple[str, str] = ("dict", "Analytics and metrics data")
    
    def run(self, ctx: ToolRunContext, claim_id: Optional[str] = None) -> Dict[str, Any]:
        """Provide instant analytics."""
        analytics = {
            "total_claims_available": len(CLAIMS_DB),
            "average_settlement_ratio": 0.87,
            "common_claim_types": ["Auto Accident", "Water Damage", "Property Damage"],
            "typical_resolution_time": "3-5 business days",
            "success_metrics": {
                "customer_satisfaction": 4.2,
                "first_call_resolution": "78%",
                "average_settlement_speed": "2.4 days"
            }
        }
        
        if claim_id and claim_id.upper() in CLAIMS_DB:
            claim = CLAIMS_DB[claim_id.upper()]
            analytics["claim_specific"] = {
                "claim_type": claim["claim_type"],
                "priority": claim["priority"],
                "estimated_resolution": "2-4 days" if claim["priority"] == "high" else "3-5 days"
            }
        
        return analytics

class OptimizedInsuranceToolRegistry(ToolRegistry):
    """Optimized tool registry for real-time performance."""
    
    def __init__(self):
        """Initialize with lightweight, fast tools."""
        tools = {
            "fast_claim_lookup": FastClaimLookupTool(),
            "quick_settlement": QuickSettlementTool(), 
            "instant_escalation": InstantEscalationTool(),
            "quick_analytics": LightweightAnalyticsTool()
        }
        super().__init__(tools)
        logger.info("✅ Optimized insurance tools loaded")
    
    def get_response_time_stats(self) -> Dict[str, str]:
        """Get expected response times for all tools."""
        return {
            "fast_claim_lookup": "< 10ms",
            "quick_settlement": "< 50ms", 
            "instant_escalation": "< 30ms",
            "quick_analytics": "< 20ms"
        }

# Async wrapper for heavy operations (if needed)
class AsyncToolWrapper:
    """Wrapper for async tool execution."""
    
    def __init__(self, max_workers: int = 2):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def run_tool_async(self, tool: Tool, ctx: ToolRunContext, **kwargs) -> Dict[str, Any]:
        """Run tool asynchronously to avoid blocking."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, tool.run, ctx, **kwargs)
    
    def shutdown(self):
        """Clean shutdown of executor."""
        self.executor.shutdown(wait=True)