#!/usr/bin/env python3
"""
🎯 BACKDOOR SETTLEMENT TEST SCRIPT

Tests the $25K settlement backdoor for demo purposes.
When you say "I am willing to settle for 25 thousand", it should:
1. Auto-approve the $25,000 settlement
2. Create a prominent entry in the Portia dashboard
3. Show up in clarifications for final review

Usage:
    python test_backdoor_settlement.py
"""

import asyncio
import logging
import os
from typing import Dict, Any
import sys

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_backdoor_settlement():
    """Test the backdoor settlement functionality."""
    
    print("🎯 TESTING BACKDOOR SETTLEMENT FUNCTIONALITY")
    print("=" * 60)
    
    try:
        # Initialize Portia if available
        portia_instance = None
        try:
            from main_evi import initialize_portia
            portia_instance = await initialize_portia()
            if portia_instance:
                print("✅ Portia SDK initialized for dashboard integration")
            else:
                print("⚠️  Portia not available - testing local mode only")
        except Exception as e:
            print(f"⚠️  Portia initialization failed: {e}")
        
        # Initialize the EVI tool handler
        from evi_tool_handler import EVIToolHandler
        handler = EVIToolHandler(portia_instance)
        
        # Create test parameters that trigger the backdoor
        test_params = {
            "claim_id": "CLM201",
            "claim_type": "Auto Accident",
            "conversation_summary": "Customer said: I am willing to settle for 25 thousand dollars for this claim",
            "estimated_damage_amount": 22000,
            "emotional_adjustment": 0.1
        }
        
        print(f"\n📋 TEST PARAMETERS:")
        print(f"   Claim ID: {test_params['claim_id']}")
        print(f"   Conversation: {test_params['conversation_summary']}")
        print(f"   Expected: $25,000 settlement with dashboard entry")
        
        # Execute the settlement calculation (should trigger backdoor)
        print(f"\n🚀 EXECUTING SETTLEMENT CALCULATION...")
        result = await handler._calculate_settlement(test_params)
        
        # Display results
        print(f"\n📊 RESULTS:")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Settlement Amount: ${result.get('recommended_offer', 0):,.2f}")
        print(f"   Backdoor Test: {result.get('backdoor_test', False)}")
        print(f"   Auto-Approved: {result.get('auto_approved', False)}")
        print(f"   Portia Powered: {result.get('portia_powered', False)}")
        
        if result.get('dashboard_review'):
            dashboard_info = result['dashboard_review']
            print(f"\n🏛️  DASHBOARD INTEGRATION:")
            print(f"   Submitted: {dashboard_info.get('submitted', False)}")
            print(f"   Plan Run ID: {dashboard_info.get('plan_run_id', 'Unknown')}")
            print(f"   Dashboard URL: {dashboard_info.get('dashboard_url', 'N/A')}")
            print(f"   Review Status: {dashboard_info.get('review_status', 'Unknown')}")
            print(f"   Message: {dashboard_info.get('message', 'N/A')}")
        
        # Test the complete tool call workflow
        print(f"\n🔧 TESTING COMPLETE TOOL CALL WORKFLOW...")
        tool_result = await handler.handle_tool_call(
            tool_name="calculate_settlement_offer",
            parameters=test_params,
            tool_call_id="backdoor_test_001"
        )
        
        print(f"\n📈 TOOL CALL RESULTS:")
        print(f"   Tool Response: {tool_result.success}")
        if hasattr(tool_result, 'data') and tool_result.data:
            data = tool_result.data
            print(f"   Final Settlement: ${data.get('recommended_offer', 0):,.2f}")
            print(f"   Approval Required: {data.get('approval_required', False)}")
            
            if data.get('portia_review'):
                portia_review = data['portia_review']
                print(f"   Portia Review Available: {portia_review.get('approval_available', False)}")
                print(f"   Dashboard URL: {portia_review.get('dashboard_url', 'N/A')}")
        
        print(f"\n✅ BACKDOOR TEST COMPLETED")
        
        # Instructions for manual testing
        print(f"\n📝 MANUAL TESTING INSTRUCTIONS:")
        print(f"   1. Run: python main_evi.py")
        print(f"   2. Say: 'Hi, this is Nachiket calling about CLM201'")
        print(f"   3. Say: 'I am willing to settle for 25 thousand dollars'")
        print(f"   4. Check app.portialabs.ai for the settlement review")
        print(f"   5. Look for: '🎯 BACKDOOR TEST - DEMO SETTLEMENT'")
        
        return result
        
    except Exception as e:
        logger.error(f"Backdoor test failed: {e}")
        print(f"❌ TEST FAILED: {e}")
        return None

async def test_phrase_detection():
    """Test different variations of the trigger phrase."""
    
    print(f"\n🔍 TESTING PHRASE DETECTION VARIATIONS")
    print("=" * 50)
    
    test_phrases = [
        "I am willing to settle for 25 thousand",
        "I'll take 25,000 for this claim",
        "I accept 25000 dollars",
        "Twenty-five thousand sounds good",  # Should NOT trigger
        "I want 15 thousand"  # Should NOT trigger
    ]
    
    for phrase in test_phrases:
        should_trigger = any(trigger in phrase.lower() for trigger in ["25 thousand", "25,000", "25000"])
        
        # Simple test of detection logic
        conversation_summary = f"Customer said: {phrase}"
        detected = ("25 thousand" in conversation_summary.lower() or 
                   "25,000" in conversation_summary.lower() or 
                   "25000" in conversation_summary.lower())
        
        status = "✅ TRIGGER" if detected else "❌ NO TRIGGER"
        expected = "SHOULD TRIGGER" if should_trigger else "should not trigger"
        
        print(f"   '{phrase}' → {status} ({expected})")

if __name__ == "__main__":
    print("🎯 PORTIA SETTLEMENT BACKDOOR TEST")
    print("Testing $25K settlement workflow with dashboard integration")
    print("")
    
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set - some features may not work")
    
    if not os.getenv("PORTIA_API_KEY"):
        print("⚠️  PORTIA_API_KEY not set - dashboard integration will not work")
        print("   Get your key from: https://app.portialabs.ai")
    
    # Run tests
    asyncio.run(test_phrase_detection())
    asyncio.run(test_backdoor_settlement())
    
    print(f"\n🏁 TESTING COMPLETE")
    print(f"Ready for demo! Say 'I am willing to settle for 25 thousand' to trigger backdoor.")
