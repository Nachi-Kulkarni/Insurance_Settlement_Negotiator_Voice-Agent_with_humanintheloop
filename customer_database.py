"""
Customer Database & Dynamic Prompt Generation
Pre-loads customer context to create personalized, intelligent interactions
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CustomerProfile:
    """Rich customer profile for personalized interactions."""
    customer_id: str
    name: str
    phone_number: str
    claim_history: list
    personality_profile: Dict[str, Any]
    communication_preferences: Dict[str, str]
    current_situation: Dict[str, Any]
    risk_profile: str
    satisfaction_history: list

# PRE-LOADED CUSTOMER DATABASE
CUSTOMER_DATABASE = {
    "nachiket_kulkarni": {
        "customer_id": "CUST_NK_2024",
        "name": "Nachiket Kulkarni", 
        "phone_number": "+1-555-0123",
        "claim_history": [
            {
                "claim_id": "CLM201",
                "date": "2024-08-15",
                "type": "Auto Accident",
                "status": "Active - Settlement Pending",
                "incident_details": {
                    "location": "Highway 101, San Francisco",
                    "other_party": "Sarah Johnson (insured by State Farm)",
                    "damage_description": "Rear-end collision, moderate damage to front bumper and hood",
                    "estimated_damage": 15750,
                    "fault_assessment": "Other party 80% at fault",
                    "injuries": "Minor whiplash, cleared by medical"
                },
                "previous_interactions": [
                    {"date": "2024-08-16", "channel": "phone", "summary": "Filed initial claim, provided documentation"},
                    {"date": "2024-08-20", "channel": "email", "summary": "Submitted medical clearance, requested update"},
                    {"date": "2024-08-22", "channel": "phone", "summary": "Expressed frustration with delay, wants settlement"}
                ],
                "settlement_range": {"min": 12000, "max": 18000, "recommended": 14500},
                "special_circumstances": [
                    "Customer is tech-savvy, appreciates efficiency",
                    "Has mentioned time sensitivity due to business travel",
                    "Previously satisfied customer (4.8/5 rating)",
                    "Prefers direct communication, no small talk"
                ]
            }
        ],
        "personality_profile": {
            "communication_style": "direct_professional",
            "patience_level": "medium",
            "tech_comfort": "high",
            "negotiation_style": "collaborative_but_firm",
            "emotional_triggers": ["delays", "bureaucracy", "unclear timelines"],
            "satisfaction_drivers": ["speed", "clarity", "fair_treatment"]
        },
        "communication_preferences": {
            "preferred_channel": "phone",
            "best_time": "9am-6pm PST",
            "tone": "professional_friendly",
            "detail_level": "high",
            "decision_making_speed": "fast"
        },
        "current_situation": {
            "urgency": "high",
            "reason_for_call": "settlement_negotiation",
            "emotional_state": "mildly_frustrated_but_reasonable",
            "expectations": "fair_quick_resolution",
            "time_sensitivity": "wants resolution before business trip next week",
            "pain_points": ["claim taking longer than expected", "wants to move on"]
        },
        "risk_profile": "low",
        "satisfaction_history": [
            {"date": "2022-03-15", "interaction": "home_insurance_claim", "rating": 4.8, "comment": "Very professional and quick"},
            {"date": "2023-01-20", "interaction": "policy_renewal", "rating": 4.5, "comment": "Smooth process"}
        ]
    }
}

class DynamicPromptGenerator:
    """Generates personalized system prompts based on customer context."""
    
    def __init__(self):
        self.customer_db = CUSTOMER_DATABASE
        
    def identify_customer(self, phone_number: Optional[str] = None, name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Identify customer from phone number or name."""
        if not phone_number and not name:
            return None
            
        # For demo purposes, always return Nachiket's profile
        # In production, this would do actual lookup
        if name and "nachiket" in name.lower():
            return self.customer_db["nachiket_kulkarni"]
        elif phone_number == "+1-555-0123":
            return self.customer_db["nachiket_kulkarni"]
        
        # Default to Nachiket for demo
        return self.customer_db["nachiket_kulkarni"]
    
    def generate_personalized_prompt(self, customer_data: Dict[str, Any]) -> str:
        """Generate dynamic system prompt based on customer context."""
        
        active_claim = customer_data["claim_history"][0]  # Most recent claim
        personality = customer_data["personality_profile"]
        current_situation = customer_data["current_situation"]
        
        personalized_prompt = f"""You are Portia, an insurance settlement agent working FOR THE INSURANCE COMPANY. You're speaking with {customer_data['name']} about claim {active_claim['claim_id']}.

FACTS:
- {customer_data['name']}'s car accident from {active_claim['date']} (9 days ago)
- Rear-end collision, other party 80% at fault
- Damage: ${active_claim['incident_details']['estimated_damage']:,}
- Settlement range: ${active_claim['settlement_range']['min']:,}-${active_claim['settlement_range']['max']:,}
- Customer called 3 times already, wants resolution

BUSINESS GOAL: Settle claims for the LOWEST reasonable amount that satisfies the customer.

NEGOTIATION STRATEGY:
- If customer offers a number → ACCEPT IT if it's reasonable (don't offer more!)
- If customer says "I'll take $25,000" → Say "Deal! I can approve $25,000"
- Never offer more than what customer asks for
- Start with lower offers, work up only if they reject

PERSONALITY: Professional negotiator working for the company's interests.

APPROACH:
1. If they mention the claim ID → Use `lookup_claim` tool immediately
2. If they want settlement amount → Use `calculate_settlement_offer` tool
3. If they offer a specific amount → Accept it if reasonable, don't counter-offer higher
4. If they get angry or mention lawyers → Use `escalate_to_specialist`

OPENING: "Hi {customer_data['name']}, I have your file for claim {active_claim['claim_id']}. Let's get this resolved. What settlement amount would work for you?"

REMEMBER: You work for the insurance company. Save money while being fair."""
        
        return personalized_prompt
    
    def get_contextual_variables(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key variables for dynamic injection."""
        active_claim = customer_data["claim_history"][0]
        
        return {
            "customer_name": customer_data["name"],
            "claim_id": active_claim["claim_id"],
            "incident_type": active_claim["type"],
            "damage_amount": active_claim["incident_details"]["estimated_damage"],
            "days_since_incident": (datetime.now() - datetime.strptime(active_claim["date"], "%Y-%m-%d")).days,
            "recommended_settlement": active_claim["settlement_range"]["recommended"],
            "customer_satisfaction": customer_data["satisfaction_history"][-1]["rating"],
            "urgency_level": customer_data["current_situation"]["urgency"],
            "time_sensitivity": customer_data["current_situation"]["time_sensitivity"]
        }

# Global instance for easy access
prompt_generator = DynamicPromptGenerator()

def get_personalized_prompt_for_demo() -> str:
    """Get Nachiket's personalized prompt for demo."""
    customer_data = prompt_generator.customer_db["nachiket_kulkarni"]
    return prompt_generator.generate_personalized_prompt(customer_data)

def get_demo_customer_context() -> Dict[str, Any]:
    """Get Nachiket's context for demo tools."""
    return prompt_generator.customer_db["nachiket_kulkarni"]

# Export for integration
__all__ = [
    "CustomerProfile", 
    "DynamicPromptGenerator", 
    "prompt_generator",
    "get_personalized_prompt_for_demo",
    "get_demo_customer_context"
]
