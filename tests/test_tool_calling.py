#!/usr/bin/env python3
"""
Test script to verify tool calling workflow for dashboard integration.
"""

import asyncio
import logging
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_calculate_settlement_tool():
    """Test the calculate_settlement_offer tool directly."""
    
    print("🔧 TESTING CALCULATE_SETTLEMENT_OFFER TOOL")
    print("=" * 50)
    
    try:
        # Initialize Portia
        portia_instance = None
        try:
            from main_evi import initialize_portia
            portia_instance = await initialize_portia()
            if portia_instance:
                print("✅ Portia SDK initialized")
            else:
                print("⚠️ Portia not available - testing local mode")
        except Exception as e:
            print(f"⚠️ Portia initialization failed: {e}")
        
        # Initialize tool handler
        from evi_tool_handler import EVIToolHandler
        handler = EVIToolHandler(portia_instance)
        
        # Test parameters that should trigger backdoor
        test_params = {
            "claim_id": "CLM201",
            "claim_type": "Auto Accident", 
            "conversation_summary": "Customer said: I am willing to settle for twenty five thousand dollars",
            "estimated_damage_amount": 22000,
            "emotional_adjustment": 0.1
        }
        
        print(f"\n📋 Testing with parameters:")
        print(f"   Conversation: {test_params['conversation_summary']}")
        print(f"   Should trigger: Backdoor test + Dashboard entry")
        
        # Call the tool directly
        print(f"\n🚀 Calling calculate_settlement_offer tool...")
        result = await handler.handle_tool_call(
            tool_name="calculate_settlement_offer",
            parameters=test_params,
            tool_call_id="test_001"
        )
        
        print(f"\n📊 TOOL CALL RESULTS:")
        print(f"   Success: {result.success}")
        if result.success and hasattr(result, 'data'):
            data = result.data
            print(f"   Settlement Amount: ${data.get('recommended_offer', 0):,.2f}")
            print(f"   Backdoor Test: {data.get('backdoor_test', False)}")
            print(f"   Auto-Approved: {data.get('auto_approved', False)}")
            print(f"   Portia Powered: {data.get('portia_powered', False)}")
            
            # Check dashboard integration
            if data.get('dashboard_review'):
                dashboard = data['dashboard_review']
                print(f"\n🏛️ DASHBOARD INTEGRATION:")
                print(f"   Submitted: {dashboard.get('submitted', False)}")
                print(f"   Plan Run ID: {dashboard.get('plan_run_id', 'N/A')}")
                print(f"   Dashboard URL: {dashboard.get('dashboard_url', 'N/A')}")
                print(f"   Review Status: {dashboard.get('review_status', 'N/A')}")
            
            if data.get('portia_review'):
                portia_review = data['portia_review']
                print(f"\n📋 PORTIA REVIEW:")
                print(f"   Available: {portia_review.get('approval_available', False)}")
                print(f"   Required: {portia_review.get('approval_required', False)}")
                print(f"   Dashboard URL: {portia_review.get('dashboard_url', 'N/A')}")
        
        print(f"\n✅ Tool calling test completed")
        
        # Instructions for next test
        print(f"\n🎯 NEXT STEPS FOR FULL TEST:")
        print(f"   1. Run: python main_evi.py")
        print(f"   2. Say: 'I am willing to settle for twenty-five thousand dollars'")
        print(f"   3. EVI should call calculate_settlement_offer tool")
        print(f"   4. Check app.portialabs.ai for dashboard entry")
        print(f"   5. Look for 'Needs Clarification' with settlement review")
        
        return True
        
    except Exception as e:
        print(f"❌ Tool calling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🎯 TOOL CALLING TEST FOR DASHBOARD INTEGRATION")
    print("Testing that calculate_settlement_offer tool creates Portia dashboard entries")
    print("")
    
    success = asyncio.run(test_calculate_settlement_tool())
    
    if success:
        print(f"\n🏁 TEST PASSED")
        print(f"Tool calling workflow is working. Now test with voice interface.")
    else:
        print(f"\n❌ TEST FAILED") 
        print(f"Tool calling needs debugging before dashboard integration will work.")
