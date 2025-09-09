"""
Settlement Review Workflow with Portia Dashboard Integration
Implements human approval for high-value settlements via Portia clarifications.
"""

import logging
from typing import Dict, Any, Optional
from portia import Portia, Config, StorageClass
from portia.clarification import ValueConfirmationClarification, CustomClarification
from portia.tool import Tool, ToolRunContext
from pydantic import BaseModel, Field
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class SettlementDecision:
    """Settlement decision with review requirements."""
    amount: float
    requires_approval: bool
    approval_threshold: float
    justification: str
    risk_factors: Dict[str, Any]
    customer_context: Dict[str, Any]

class SettlementReviewArgs(BaseModel):
    settlement_amount: float = Field(..., description="Proposed settlement amount")
    claim_id: str = Field(..., description="Claim ID for this settlement")
    customer_name: str = Field(..., description="Customer name")
    claim_details: Dict[str, Any] = Field(..., description="Claim context and details")
    risk_assessment: Dict[str, Any] = Field(default_factory=dict, description="Risk factors")

class PortiaSettlementReviewTool(Tool):
    """Tool that creates human review requests for high-value settlements."""
    
    id: str = "portia_settlement_review"
    name: str = "Portia Settlement Review"
    description: str = "Creates human approval requests for settlements requiring review"
    args_schema: type[BaseModel] = SettlementReviewArgs
    output_schema: tuple[str, str] = ("dict", "Settlement decision with approval status")
    
    def __init__(self, approval_threshold: float = 15000.0):
        super().__init__()
        self._approval_threshold = approval_threshold
    
    @property
    def approval_threshold(self) -> float:
        return self._approval_threshold
    
    def run(self, ctx: ToolRunContext, 
            settlement_amount: float,
            claim_id: str, 
            customer_name: str,
            claim_details: Dict[str, Any],
            risk_assessment: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process settlement and create review request if needed."""
        
        risk_assessment = risk_assessment or {}
        requires_approval = settlement_amount > self.approval_threshold
        
        if not requires_approval:
            # Auto-approve settlements under threshold
            return {
                "approved": True,
                "amount": settlement_amount,
                "approval_required": False,
                "review_type": "auto_approved",
                "message": f"Settlement of ${settlement_amount:,.2f} auto-approved (under ${self.approval_threshold:,.2f} threshold)"
            }
        
        # Create clarification for human review via Portia dashboard
        review_data = {
            "settlement_amount": settlement_amount,
            "claim_id": claim_id,
            "customer_name": customer_name,
            "claim_details": claim_details,
            "risk_assessment": risk_assessment,
            "approval_threshold": self.approval_threshold,
            "timestamp": str(ctx.plan_run.id) if ctx.plan_run else "unknown"
        }
        
        # Enhanced guidance for backdoor test recognition
        is_backdoor = risk_assessment.get('backdoor_test', False)
        guidance_header = "🎯 BACKDOOR TEST - DEMO SETTLEMENT" if is_backdoor else "🏛️ SETTLEMENT REVIEW REQUIRED"
        
        # This creates a clarification that appears on app.portialabs.ai dashboard
        clarification = ValueConfirmationClarification(
            argument_name="settlement_approval",
            user_guidance=f"""
{guidance_header}

Customer: {customer_name}
Claim ID: {claim_id}
Proposed Amount: ${settlement_amount:,.2f}

DETAILS:
• Claim Type: {claim_details.get('type', 'Unknown')}
• Damage Amount: ${claim_details.get('damage_amount', 0):,.2f}
• Incident Date: {claim_details.get('date', 'Unknown')}
• Days Pending: {claim_details.get('days_pending', 'Unknown')}
{f"• TEST SCENARIO: {claim_details.get('test_scenario', 'N/A')}" if is_backdoor else ""}

RISK FACTORS:
• Litigation Risk: {risk_assessment.get('litigation_risk', risk_assessment.get('litigation_probability', 'Unknown'))}
• Customer Satisfaction: {risk_assessment.get('customer_satisfaction', 'Unknown')}
• Urgency Level: {risk_assessment.get('urgency', 'Unknown')}
{f"• Settlement Type: {risk_assessment.get('settlement_type', 'Unknown')}" if is_backdoor else ""}

{f"🎯 BACKDOOR TEST NOTES: {risk_assessment.get('test_notes', 'Demo scenario')}" if is_backdoor else f"APPROVAL REQUIRED: Amount exceeds ${self.approval_threshold:,.2f} threshold"}

Approve this settlement? {"(Demo Test - Auto-Approved)" if is_backdoor else ""}
            """.strip(),
            response=settlement_amount,  # Pre-populate with the proposed amount
            plan_run_id=ctx.plan_run.id if ctx.plan_run else None,
            source="Settlement Review System" + (" - BACKDOOR TEST" if is_backdoor else "")
        )
        
        # Return clarification JSON that gets processed by Portia
        return {
            "approved": False,
            "amount": settlement_amount,
            "approval_required": True,
            "review_type": "human_review_pending",
            "clarification": clarification.model_dump(),
            "dashboard_url": "https://app.portialabs.ai",
            "message": f"Settlement of ${settlement_amount:,.2f} requires human approval. Review pending on Portia dashboard."
        }

class SettlementReviewWorkflow:
    """Manages settlement review workflow with Portia dashboard integration."""
    
    def __init__(self, portia_instance: Portia, approval_threshold: float = 15000.0):
        self.portia = portia_instance
        self.approval_threshold = approval_threshold
        self.review_tool = PortiaSettlementReviewTool(approval_threshold)
        
        # Ensure cloud storage is enabled for dashboard visibility
        if hasattr(self.portia.config, 'storage_class'):
            if self.portia.config.storage_class != StorageClass.CLOUD:
                logger.warning("⚠️ Storage not set to CLOUD - reviews may not appear on dashboard")
        
    async def request_settlement_review(self, 
                                      settlement_amount: float,
                                      claim_id: str,
                                      customer_name: str,
                                      claim_details: Dict[str, Any],
                                      risk_assessment: Dict[str, Any] = None) -> Dict[str, Any]:
        """Request settlement review - create direct clarification for immediate dashboard visibility."""
        
        try:
            # Create simple task that should create clarifications when it can't proceed
            is_backdoor = risk_assessment.get('backdoor_test', False) if risk_assessment else False
            guidance_header = "🎯 BACKDOOR TEST - DEMO SETTLEMENT" if is_backdoor else "🏛️ SETTLEMENT REVIEW REQUIRED"
            
            logger.info(f"Creating settlement clarification task: ${settlement_amount:,.2f}")
            
            # Task specifically designed to create clarifications
            clarification_task = f"""
URGENT SETTLEMENT APPROVAL REQUIRED

{guidance_header}

I need explicit human authorization before I can proceed with this high-value settlement.

Settlement Details:
- Customer: {customer_name}
- Claim ID: {claim_id}
- Settlement Amount: ${settlement_amount:,.2f}
- Claim Type: {claim_details.get('type', 'Auto Accident')}
- Original Damage: ${claim_details.get('damage_amount', 0):,.2f}
- Days Pending: {claim_details.get('days_pending', 'Unknown')}
- Risk Assessment: {risk_assessment.get('litigation_risk', 'Low') if risk_assessment else 'Low'}
{f"- Test Notes: {risk_assessment.get('test_notes', 'Testing clarification generation')}" if is_backdoor else ""}

CRITICAL: I cannot proceed without explicit human approval. This settlement exceeds my authorization limit.

I need you to manually review and approve this settlement before I can continue. Please provide explicit confirmation.

WAITING FOR HUMAN INPUT TO CONTINUE...
            """.strip()
            
            try:
                # Create task run that should require clarification
                logger.info(f"Creating task that requires human clarification")
                plan_run = await self.portia.arun(clarification_task)
                plan_run_id = plan_run.id
                logger.info(f"✅ Settlement task created: {plan_run_id}")
                
                # Check final state
                plan_state = plan_run.state.value if hasattr(plan_run.state, 'value') else str(plan_run.state)
                clarification_count = len(plan_run.clarifications) if hasattr(plan_run, 'clarifications') else 0
                
                logger.info(f"Settlement task state: {plan_state}, Clarifications: {clarification_count}")
                
                # Determine expected dashboard tab
                expected_tab = "Needs Clarification" if (clarification_count > 0 or 
                                                       plan_state in ["NEED_CLARIFICATION", "NOT_STARTED"]) else "Success"
                
                return {
                    "workflow_started": True,
                    "plan_run_id": plan_run.id,
                    "dashboard_url": "https://app.portialabs.ai",
                    "status": plan_state,
                    "message": f"Settlement review created. Plan run: {plan_run.id}",
                    "guidance_header": guidance_header,
                    "clarifications": clarification_count,
                    "settlement_amount": settlement_amount,
                    "customer_name": customer_name,
                    "expected_tab": expected_tab,
                    "note": f"Status {plan_state} should appear in {expected_tab} tab"
                }
                
            except Exception as inner_e:
                logger.error(f"Settlement task creation failed: {inner_e}")
                return {
                    "workflow_started": False,
                    "error": str(inner_e),
                    "message": f"Could not create settlement task - manual review required for ${settlement_amount:,.2f} settlement"
                }
            
        except Exception as e:
            logger.error(f"Settlement review creation failed: {e}")
            return {
                "workflow_started": False,
                "error": str(e),
                "fallback_message": "Review creation failed - manual approval required"
            }
    
    def check_dashboard_access(self) -> Dict[str, Any]:
        """Verify dashboard access and provide connection info."""
        return {
            "dashboard_url": "https://app.portialabs.ai",
            "api_key_required": "PORTIA_API_KEY environment variable",
            "storage_class": getattr(self.portia.config, 'storage_class', 'unknown'),
            "cloud_enabled": hasattr(self.portia.config, 'storage_class') and 
                           self.portia.config.storage_class == StorageClass.CLOUD,
            "instructions": [
                "1. Set PORTIA_API_KEY in your environment",
                "2. Configure StorageClass.CLOUD in Portia config",
                "3. Run settlement workflow",
                "4. Check app.portialabs.ai for review requests",
                "5. Approve/reject settlements from dashboard"
            ]
        }

# Integration helper for existing EVI tool handler
def integrate_settlement_review_workflow(evi_tool_handler, portia_instance: Portia):
    """Integrate settlement review into existing EVI tool handler."""
    
    if not portia_instance:
        logger.warning("No Portia instance - settlement review not available")
        return False
    
    # Add settlement review workflow
    evi_tool_handler.settlement_review = SettlementReviewWorkflow(
        portia_instance=portia_instance,
        approval_threshold=15000.0  # $15K threshold
    )
    
    logger.info("✅ Settlement review workflow integrated with Portia dashboard")
    return True

def create_cloud_config() -> Config:
    """Create Portia config with cloud storage for dashboard integration."""
    import os
    
    config = Config.from_default()
    
    # Enable cloud storage for dashboard visibility
    if hasattr(config, 'storage_class'):
        config.storage_class = StorageClass.CLOUD
    
    # Ensure Portia API key is set
    if not os.getenv("PORTIA_API_KEY"):
        logger.warning("⚠️ PORTIA_API_KEY not set - dashboard features may not work")
    
    return config

# Export for integration
__all__ = [
    "SettlementReviewWorkflow",
    "PortiaSettlementReviewTool", 
    "integrate_settlement_review_workflow",
    "create_cloud_config",
    "SettlementDecision"
]
