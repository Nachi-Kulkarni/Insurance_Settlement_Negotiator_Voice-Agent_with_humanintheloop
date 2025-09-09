"""
EVI Tool Handler - Maps EVI function calls to business logic.
This replaces the complex background ThreadPoolExecutor with simple tool execution.
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass
from portia_tools import OptimizedInsuranceToolRegistry
from portia.tool import ToolRunContext
import time

logger = logging.getLogger(__name__)

@dataclass
class ToolExecutionResult:
    """Result of tool execution."""
    success: bool
    data: Dict[str, Any]
    execution_time: float
    tool_name: str

class EVIToolHandler:
    """Handles EVI tool calls and maps them to business logic."""
    
    def __init__(self, portia_instance=None):
        """Initialize with optional Portia instance for advanced processing."""
        self.tool_registry = OptimizedInsuranceToolRegistry()
        self.portia_instance = portia_instance
        self.execution_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "average_execution_time": 0.0
        }
    
    async def handle_tool_call(self, tool_name: str, parameters: Dict[str, Any], tool_call_id: str) -> ToolExecutionResult:
        """Handle a tool call from EVI."""
        import time
        start_time = time.time()
        
        try:
            self.execution_stats["total_calls"] += 1
            logger.info(f"🔧 Executing tool: {tool_name} with params: {parameters}")
            
            # Map EVI tool names to our internal tools
            result = await self._execute_mapped_tool(tool_name, parameters)
            
            execution_time = time.time() - start_time
            self._update_stats(execution_time, success=True)
            
            logger.info(f"✅ Tool {tool_name} executed successfully in {execution_time:.3f}s")
            
            return ToolExecutionResult(
                success=True,
                data=result,
                execution_time=execution_time,
                tool_name=tool_name
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_stats(execution_time, success=False)
            
            logger.error(f"❌ Tool {tool_name} failed: {e}")
            
            return ToolExecutionResult(
                success=False,
                data={"error": str(e), "tool_name": tool_name},
                execution_time=execution_time,
                tool_name=tool_name
            )
    
    async def _execute_mapped_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the mapped tool based on EVI tool name."""
        
        # Map to actual Portia tool IDs
        if tool_name in ["lookup_claim", "fast_claim_lookup"]:
            return await self._lookup_claim(parameters)
            
        elif tool_name in ["calculate_settlement_offer", "quick_settlement"]:
            return await self._calculate_settlement(parameters)
            
        elif tool_name in ["escalate_to_specialist", "instant_escalation"]:
            return await self._escalate_case(parameters)
            
        elif tool_name in ["create_payment_plan", "quick_analytics"]:
            return await self._create_payment_plan(parameters)
            
        elif tool_name in ["request_human_intervention"]:
            return await self._request_human_intervention(parameters)
            
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _lookup_claim(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Look up claim details with customer context."""
        claim_id = params.get("claim_id")
        
        # Check for personalized customer context first
        try:
            from customer_database import get_demo_customer_context
            customer_context = get_demo_customer_context()
            
            # If claim ID matches our known customer, return rich context
            if claim_id and claim_id.upper() == "CLM201":
                active_claim = customer_context["claim_history"][0]
                return {
                    "success": True,
                    "claim": active_claim,
                    "customer_context": {
                        "name": customer_context["name"],
                        "satisfaction_history": customer_context["satisfaction_history"][-1]["rating"],
                        "days_since_incident": 9,  # August 15 to August 24
                        "previous_interactions": len(active_claim["previous_interactions"]),
                        "urgency_reason": customer_context["current_situation"]["time_sensitivity"]
                    },
                    "personalized_response": f"I have {customer_context['name']}'s complete file for claim {claim_id}. This rear-end collision from {active_claim['date']} has been pending for 9 days.",
                    "lookup_time": "instant"
                }
        except ImportError:
            pass
        
        # Use fast lookup tool
        tools_list = self.tool_registry.get_tools()
        tool = next((t for t in tools_list if t.id == "fast_claim_lookup"), None)
        if not tool:
            return {"error": "Fast claim lookup tool not found"}
        
        # Create a minimal context for testing
        from portia import Config
        config = Config(
            llm_provider="openai",
            openai_api_key="dummy_key_for_testing",
            default_model="gpt-3.5-turbo"
        )
        ctx = ToolRunContext(
            end_user={"external_id": "test_user", "id": "user_test_123"},
            plan_run={"id": "run_test_123", "plan_id": "plan_test_123", "end_user_id": "user_test_123"},
            plan={"id": "plan_test_123", "plan_context": {}, "steps": []},
            config=config,
            clarifications=[]
        )
        result = tool.run(ctx, claim_id=claim_id)
        
        # Enhance result with additional context for EVI
        if result.get("success") and "claim" in result:
            claim = result["claim"]
            enhanced_result = {
                **result,
                "summary": f"Found claim {claim['claim_id']} for {claim['claimant_name']}. {claim['claim_type']} with estimated damage of ${claim['estimated_damage']:,}.",
                "next_actions": ["calculate_settlement_offer", "negotiate_settlement"],
                "can_settle_immediately": claim.get("priority") != "complex"
            }
            return enhanced_result
        
        return result
    
    async def _calculate_settlement(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate settlement offer with Portia-powered intelligence."""
        
        # 🎯 BACKDOOR TEST: Check for $25K settlement amount or phrase
        estimated_damage = params.get("estimated_damage_amount", 0)
        claim_type = params.get("claim_type", "").lower()
        damage_description = params.get("damage_description", "").lower()
        conversation_summary = params.get("conversation_summary", "").lower()
        
        # Check if this is a $25K settlement request
        backdoor_triggers = [
            estimated_damage == 25000,  # Direct amount match
            "25000" in str(params),  # Any parameter contains 25000
            "25 thousand" in conversation_summary,
            "twenty five thousand" in conversation_summary, 
            "twenty-five thousand" in conversation_summary,
            "25k" in conversation_summary,
            "$25,000" in conversation_summary,
            "$25000" in conversation_summary
        ]
        
        if any(backdoor_triggers):
            logger.info("🚀 BACKDOOR TRIGGERED: $25K settlement test mode activated")
            logger.info(f"🎯 Settlement amount: ${estimated_damage}, params: {params}")
            return await self._backdoor_settlement_test(params)
        
        # Try Portia-powered settlement analysis first (HACKATHON FEATURE)
        if self.portia_instance:
            try:
                from portia_settlement_agent import SettlementContext, PortiaSettlementAgent
                
                # Create rich context for Portia analysis
                settlement_context = SettlementContext(
                    claim_id=params.get("claim_id", "GENERAL"),
                    claim_type=params.get("claim_type", "general"),
                    damage_amount=params.get("estimated_damage_amount", 10000),
                    claimant_emotions=params.get("emotional_state", {}),
                    conversation_history=params.get("conversation_summary", ""),
                    policy_details={"standard_coverage": True},
                    previous_negotiations=[],
                    market_conditions={"current_settlement_rate": 0.85}
                )
                
                # Use Portia for intelligent settlement analysis
                portia_agent = PortiaSettlementAgent(self.portia_instance)
                portia_result = await portia_agent.analyze_settlement_with_portia(settlement_context)
                
                if portia_result.get("portia_driven"):
                    return {
                        "success": True,
                        "portia_powered": True,
                        "recommended_offer": settlement_context.damage_amount * 0.85,
                        "portia_strategy": portia_result,
                        "competitive_advantage": "AI-optimized settlement strategy",
                        "reasoning": "Portia SDK analyzed claim context, emotions, and risk factors for optimal settlement"
                    }
                    
            except Exception as e:
                logger.warning(f"Portia settlement analysis failed, falling back to standard: {e}")
        
        # Fallback to standard calculation with customer context enhancement
        claim_type = params.get("claim_type", "general")
        damage_description = params.get("damage_description", "")
        emotional_adjustment = params.get("emotional_adjustment", 0.0)
        estimated_damage = params.get("estimated_damage_amount")
        claim_id = params.get("claim_id")
        
        # Enhance with customer context if available
        try:
            from customer_database import get_demo_customer_context
            customer_context = get_demo_customer_context()
            
            if claim_id and claim_id.upper() == "CLM201":
                active_claim = customer_context["claim_history"][0]
                # Use customer-specific data
                estimated_damage = active_claim["incident_details"]["estimated_damage"]
                claim_type = active_claim["type"]
                # Add frustration adjustment for delay
                emotional_adjustment = max(emotional_adjustment, 0.1)  # 10% for 9-day delay
                
                logger.info(f"🎯 Using personalized context for {customer_context['name']}")
        except ImportError:
            pass
        
        # Use quick settlement tool
        tools_list = self.tool_registry.get_tools()
        tool = next((t for t in tools_list if t.id == "quick_settlement"), None)
        if not tool:
            return {"error": "Quick settlement tool not found"}
        
        # Create a minimal context for testing
        from portia import Config
        import os
        config = Config(
            llm_provider="openai",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            default_model="gpt-4o"
        )
        ctx = ToolRunContext(
            end_user={"external_id": "test_user", "id": "user_test_123"},
            plan_run={"id": "run_test_123", "plan_id": "plan_test_123", "end_user_id": "user_test_123"},
            plan={"id": "plan_test_123", "plan_context": {}, "steps": []},
            config=config,
            clarifications=[]
        )
        result = tool.run(
            ctx,
            claim_id=claim_id,
            incident_type=claim_type,
            damage_amount=estimated_damage,
            emotional_adjustment=emotional_adjustment
        )
        
        # Enhance for EVI response with Portia settlement review
        if result.get("success"):
            offer = result["recommended_offer"]
            
            # Check if settlement review is needed via Portia
            approval_info = await self._check_settlement_approval(offer, claim_id, parameters)
            
            enhanced_result = {
                **result,
                "summary": f"Calculated settlement offer of ${offer:,.2f} for {claim_type} claim.",
                "justification": result.get("reasoning", "Based on standard settlement calculations"),
                "negotiation_room": {
                    "can_increase_to": offer * 1.15,  # 15% room for negotiation
                    "minimum_acceptable": offer * 0.85  # Don't go below 85%
                },
                "approval_required": offer > 15000,  # Portia review threshold
                "portia_review": approval_info
            }
            return enhanced_result
        
        return result
    
    async def _escalate_case(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Escalate case to specialist."""
        reason = params.get("reason", "general")
        conversation_summary = params.get("conversation_summary", "")
        urgency_level = params.get("urgency_level", "medium")
        claim_id = params.get("claim_id")
        
        # Map urgency to trigger
        urgency_to_trigger = {
            "low": "general",
            "medium": "complex", 
            "high": "distress",
            "critical": "legal"
        }
        trigger = urgency_to_trigger.get(urgency_level, "general")
        
        # Use instant escalation tool
        tools_list = self.tool_registry.get_tools()
        tool = next((t for t in tools_list if t.id == "instant_escalation"), None)
        if not tool:
            return {"error": "Instant escalation tool not found"}
        
        # Create a minimal context for testing
        from portia import Config
        import os
        config = Config(
            llm_provider="openai",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            default_model="gpt-4o"
        )
        ctx = ToolRunContext(
            end_user={"external_id": "test_user", "id": "user_test_123"},
            plan_run={"id": "run_test_123", "plan_id": "plan_test_123", "end_user_id": "user_test_123"},
            plan={"id": "plan_test_123", "plan_context": {}, "steps": []},
            config=config,
            clarifications=[]
        )
        result = tool.run(ctx, claim_id=claim_id, trigger=trigger)
        
        # Enhance for EVI
        if result.get("success"):
            escalation = result["escalation"]
            enhanced_result = {
                **result,
                "immediate_action": "transfer_to_specialist",
                "estimated_wait_time": escalation.get("sla", "Unknown"),
                "specialist_type": escalation.get("assigned_department", "General Support"),
                "conversation_should_end": True,  # Signal to EVI to wrap up
                "transfer_message": result.get("user_message", "Your case has been escalated.")
            }
            return enhanced_result
        
        return result
    
    async def _create_payment_plan(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create payment plan options."""
        settlement_amount = params.get("settlement_amount", 15000)
        plan_type = params.get("plan_type", "monthly")
        
        # Generate payment plan options
        plans = {}
        
        if plan_type == "monthly" or plan_type == "quarterly":
            periods = 3 if plan_type == "monthly" else 2
            monthly_amount = settlement_amount / periods
            plans["installment"] = {
                "total_amount": settlement_amount,
                "payment_amount": monthly_amount,
                "frequency": plan_type,
                "number_of_payments": periods,
                "description": f"${monthly_amount:,.2f} per {plan_type[:-2]} for {periods} {plan_type}s"
            }
        
        if plan_type == "expedited":
            expedited_amount = settlement_amount * 0.98  # 2% discount for speed
            plans["expedited"] = {
                "total_amount": expedited_amount,
                "processing_time": "48 hours",
                "discount_amount": settlement_amount - expedited_amount,
                "description": f"${expedited_amount:,.2f} with 48-hour processing (${settlement_amount - expedited_amount:,.2f} processing discount)"
            }
        
        # Add standard option
        plans["standard"] = {
            "total_amount": settlement_amount,
            "processing_time": "5 business days",
            "description": f"${settlement_amount:,.2f} with standard processing"
        }
        
        return {
            "success": True,
            "payment_plans": plans,
            "recommended_plan": "standard",
            "summary": f"Created {len(plans)} payment options for ${settlement_amount:,.2f} settlement",
            "requires_approval": settlement_amount > 25000
        }
    
    def _update_stats(self, execution_time: float, success: bool):
        """Update execution statistics."""
        if success:
            self.execution_stats["successful_calls"] += 1
        
        # Update average execution time
        total_calls = self.execution_stats["total_calls"]
        current_avg = self.execution_stats["average_execution_time"]
        new_avg = ((current_avg * (total_calls - 1)) + execution_time) / total_calls
        self.execution_stats["average_execution_time"] = new_avg
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        total = self.execution_stats["total_calls"]
        successful = self.execution_stats["successful_calls"]
        success_rate = (successful / total * 100) if total > 0 else 0
        
        return {
            "total_tool_calls": total,
            "successful_calls": successful,
            "success_rate_percent": round(success_rate, 1),
            "average_execution_time_ms": round(self.execution_stats["average_execution_time"] * 1000, 1),
            "tool_registry_stats": self.tool_registry.get_response_time_stats()
        }
    
    async def run_comprehensive_analysis(self, user_input: str, conversation_context: str) -> Dict[str, Any]:
        """Run comprehensive analysis using Portia if available (optional background enhancement)."""
        if not self.portia_instance:
            return {"available": False, "message": "Comprehensive analysis not available"}
        
        try:
            # This is the ONLY place we use Portia now - for deep analysis, not responses
            task_description = f"""
            COMPREHENSIVE ANALYSIS REQUEST:
            
            User Input: "{user_input}"
            Conversation Context: "{conversation_context}"
            
            Please provide:
            1. Sentiment analysis and emotional intelligence insights
            2. Risk assessment for this claim scenario
            3. Negotiation strategy recommendations
            4. Compliance and regulatory considerations
            5. Customer satisfaction optimization suggestions
            
            This is for background analysis only - do not generate responses.
            """
            
            # Run in background (non-blocking)
            loop = asyncio.get_event_loop()
            from concurrent.futures import ThreadPoolExecutor
            
            with ThreadPoolExecutor(max_workers=1) as executor:
                plan_run = await loop.run_in_executor(
                    executor,
                    self.portia_instance.run,
                    task_description
                )
            
            return {
                "available": True,
                "analysis_id": getattr(plan_run, 'id', 'unknown'),
                "insights": "Comprehensive analysis completed",
                "used_for": "background_enhancement_only"
            }
            
        except Exception as e:
            logger.debug(f"Comprehensive analysis error: {e}")
            return {"available": False, "error": str(e)}
    
    async def _request_human_intervention(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Request immediate human intervention for uncontrollable situations."""
        try:
            from human_intervention_handler import HumanInterventionHandler, InterventionTrigger
            
            trigger = params.get("trigger", "agent_failure")
            urgency_level = params.get("urgency_level", "high")
            conversation_summary = params.get("conversation_summary", "Customer situation requires human intervention")
            emotional_state = params.get("emotional_state", {"distress": 0.9})
            failure_reason = params.get("failure_reason", "AI agent unable to proceed")
            customer_threats = params.get("customer_threats")
            claim_id = params.get("claim_id")
            
            # Create intervention handler
            intervention_handler = HumanInterventionHandler()
            
            # Map trigger string to enum
            try:
                intervention_trigger = InterventionTrigger(trigger)
            except ValueError:
                intervention_trigger = InterventionTrigger.AGENT_FAILURE
            
            # Trigger intervention
            result = await intervention_handler.trigger_intervention(
                trigger=intervention_trigger,
                conversation_summary=conversation_summary,
                emotional_state=emotional_state,
                claim_id=claim_id,
                customer_threats=customer_threats,
                agent_failure_reason=failure_reason
            )
            
            # Log critical intervention
            logger.critical(f"🚨 HUMAN INTERVENTION ACTIVATED: {trigger}")
            logger.critical(f"📞 Customer will be transferred to human specialist")
            logger.critical(f"⏱️ Expected response time: {result.get('estimated_response_time', '< 2 minutes')}")
            
            # Enhanced result for EVI response
            enhanced_result = {
                **result,
                "immediate_action": "transfer_to_human",
                "agent_status": "intervention_requested", 
                "customer_message": result.get("handoff_message", "Transferring to specialist..."),
                "stop_ai_conversation": True,
                "human_takeover": True,
                "intervention_summary": {
                    "trigger": trigger,
                    "urgency": urgency_level,
                    "emotional_state": emotional_state,
                    "claim_id": claim_id,
                    "time_requested": time.time()
                }
            }
            
            return enhanced_result
        
        except Exception as e:
            logger.error(f"Human intervention request failed: {e}")
            return {
                "success": False,
                "error": "Unable to request human intervention",
                "fallback_message": "I'm going to transfer you to a specialist right away. Please hold the line."
            }
    
    async def _check_settlement_approval(self, settlement_amount: float, claim_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check if settlement requires Portia dashboard approval."""
        try:
            if not self.portia_instance:
                return {
                    "approval_available": False,
                    "message": "Portia review not available - proceeding with standard approval"
                }
            
            # Import settlement review workflow
            from settlement_review_workflow import SettlementReviewWorkflow
            
            # Initialize workflow if not already available
            if not hasattr(self, 'settlement_review'):
                self.settlement_review = SettlementReviewWorkflow(
                    portia_instance=self.portia_instance,
                    approval_threshold=15000.0
                )
            
            # Get customer context for review
            try:
                from customer_database import get_demo_customer_context
                customer_context = get_demo_customer_context()
                customer_name = customer_context["name"]
                claim_details = {
                    "type": parameters.get("claim_type", "Auto Accident"),
                    "damage_amount": parameters.get("estimated_damage_amount", 15000),
                    "date": "2024-08-15",
                    "days_pending": 9
                }
            except ImportError:
                customer_name = "Customer"
                claim_details = {
                    "type": parameters.get("claim_type", "Unknown"),
                    "damage_amount": parameters.get("estimated_damage_amount", 0)
                }
            
            # Risk assessment based on parameters
            risk_assessment = {
                "emotional_adjustment": parameters.get("emotional_adjustment", 0.0),
                "urgency": "high" if settlement_amount > 18000 else "medium",
                "customer_satisfaction": 4.8  # From customer context
            }
            
            # Request settlement review
            review_result = await self.settlement_review.request_settlement_review(
                settlement_amount=settlement_amount,
                claim_id=claim_id or "UNKNOWN",
                customer_name=customer_name,
                claim_details=claim_details,
                risk_assessment=risk_assessment
            )
            
            if settlement_amount > 15000:
                logger.info(f"🏛️ Settlement ${settlement_amount:,.2f} requires Portia dashboard approval")
                return {
                    "approval_available": True,
                    "approval_required": True,
                    "dashboard_url": "https://app.portialabs.ai",
                    "plan_run_id": review_result.get("plan_run_id"),
                    "message": f"Settlement of ${settlement_amount:,.2f} submitted for review on Portia dashboard",
                    "review_status": review_result
                }
            else:
                logger.info(f"✅ Settlement ${settlement_amount:,.2f} auto-approved (under threshold)")
                return {
                    "approval_available": True,
                    "approval_required": False,
                    "message": f"Settlement of ${settlement_amount:,.2f} auto-approved"
                }
                
        except Exception as e:
            logger.error(f"Settlement approval check failed: {e}")
            return {
                "approval_available": False,
                "error": str(e),
                "message": "Settlement approval system unavailable - proceeding with manual review"
            }
    
    async def _backdoor_settlement_test(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """🎯 BACKDOOR TEST: Auto-approve $25K settlement for demo purposes."""
        logger.info("🚀 EXECUTING BACKDOOR TEST: $25,000 settlement with Portia dashboard integration")
        
        # Force settlement amount to exactly $25,000
        settlement_amount = 25000.0
        claim_id = params.get("claim_id", "CLM201")
        
        try:
            # Get customer context for realistic demo
            from customer_database import get_demo_customer_context
            customer_context = get_demo_customer_context()
            customer_name = customer_context["name"]
            
            claim_details = {
                "type": "Auto Accident - High Value Settlement",
                "damage_amount": 22000,  # Original damage
                "settlement_adjustment": 3000,  # Additional for delay/inconvenience
                "date": "2024-08-15",
                "days_pending": 9,
                "backdoor_test": True,
                "test_scenario": "Customer willing to settle for $25K"
            }
        except ImportError:
            customer_name = "Demo Customer"
            claim_details = {
                "type": "Auto Accident - Test Settlement",
                "damage_amount": 22000,
                "backdoor_test": True
            }
        
        # Create Portia clarification for dashboard visibility
        if self.portia_instance:
            try:
                from settlement_review_workflow import SettlementReviewWorkflow
                
                # Initialize workflow if not already available
                if not hasattr(self, 'settlement_review'):
                    self.settlement_review = SettlementReviewWorkflow(
                        portia_instance=self.portia_instance,
                        approval_threshold=15000.0
                    )
                
                # Enhanced risk assessment for high-value settlement
                risk_assessment = {
                    "settlement_type": "customer_initiated_high_value",
                    "emotional_adjustment": 0.15,  # 15% for customer satisfaction
                    "urgency": "high",
                    "customer_satisfaction": 4.8,
                    "litigation_risk": "low",  # Customer willing to settle
                    "backdoor_test": True,
                    "test_notes": "Customer verbally agreed to $25K - excellent negotiation outcome"
                }
                
                # Submit to Portia dashboard for review (even though it's a backdoor test)
                review_result = await self.settlement_review.request_settlement_review(
                    settlement_amount=settlement_amount,
                    claim_id=claim_id,
                    customer_name=customer_name,
                    claim_details=claim_details,
                    risk_assessment=risk_assessment
                )
                
                logger.info(f"✅ BACKDOOR TEST: $25K settlement submitted to Portia dashboard")
                logger.info(f"📋 Dashboard URL: https://app.portialabs.ai")
                logger.info(f"🆔 Plan Run ID: {review_result.get('plan_run_id', 'Unknown')}")
                
                # Return successful settlement with dashboard info
                return {
                    "success": True,
                    "recommended_offer": settlement_amount,
                    "backdoor_test": True,
                    "auto_approved": True,
                    "portia_powered": True,
                    "reasoning": f"🎯 BACKDOOR TEST: Customer offered $25K settlement. ACCEPTED immediately (smart business move!).",
                    "customer_agreement": "Customer offered $25,000 - DEAL ACCEPTED",
                    "business_win": "Saved company money by accepting customer's offer without negotiating higher",
                    "dashboard_review": {
                        "submitted": True,
                        "plan_run_id": review_result.get("plan_run_id"),
                        "dashboard_url": "https://app.portialabs.ai",
                        "review_status": "submitted_for_final_approval",
                        "message": "Settlement appears in Portia dashboard clarifications for final approval"
                    },
                    "competitive_advantage": "Portia SDK enabled rapid high-value settlement negotiation",
                    "demo_notes": "Perfect demo scenario - customer initiated high-value settlement with dashboard integration"
                }
                
            except Exception as e:
                logger.error(f"Backdoor test Portia integration failed: {e}")
        
        # Fallback even for backdoor test
        logger.info("🔄 BACKDOOR TEST: Fallback mode - no Portia dashboard integration")
        return {
            "success": True,
            "recommended_offer": settlement_amount,
            "backdoor_test": True,
            "auto_approved": True,
            "reasoning": "🎯 BACKDOOR TEST: $25K settlement auto-approved for demo",
            "customer_agreement": "Customer verbally agreed to $25,000 settlement",
            "demo_notes": "Backdoor test executed successfully (no Portia dashboard available)"
        }

# Convenience function for easy integration
async def handle_evi_tool_call(tool_name: str, parameters: Dict[str, Any], tool_call_id: str, portia_instance=None) -> Dict[str, Any]:
    """Convenience function to handle EVI tool calls."""
    handler = EVIToolHandler(portia_instance)
    result = await handler.handle_tool_call(tool_name, parameters, tool_call_id)
    
    return {
        "success": result.success,
        "content": json.dumps(result.data),
        "execution_time": result.execution_time,
        "tool_name": result.tool_name
    }
