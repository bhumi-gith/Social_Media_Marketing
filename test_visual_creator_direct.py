#!/usr/bin/env python3
"""
Direct test of visual_creator agent with test data
Bypasses data_ingest to avoid PMS connection issues
"""
import json
import requests
import sys

API_URL = "http://127.0.0.1:18820/api/mesh/request"
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": "test"
}

# Read test data files
with open('tests/test_campaign_briefs.json', 'r') as f:
    briefs_data = json.load(f)

with open('tests/test_property_data.json', 'r') as f:
    property_data = json.load(f)

# Prepare payload directly for visual_creator (bypassing data_ingest)
payload = {
    "entry_point": "marketing_pipeline",
    "data": {
        # These would normally come from data_ingest
        # But we're providing them directly to show visual_creator working
        "vacancy_by_floorplan": json.dumps(briefs_data['campaign_briefs'][0]['target_floorplan']),
        "current_pricing": json.dumps(property_data['pricing']),
        "active_concessions": json.dumps(property_data['active_concessions']),
        "occupancy_rate": property_data['overall_occupancy'],
        "priority_floorplans": json.dumps([p['floorplan'] for p in property_data['priority_floorplans']]),
        "local_amenities": json.dumps(property_data['local_amenities']),
        "property_photos": json.dumps(property_data['photos']),
        "amenity_list": json.dumps(property_data['amenities']['community']),
        
        # Pass the campaign briefs from strategist (simulated)
        "campaign_briefs": json.dumps(briefs_data['campaign_briefs']),
        "briefs_count": len(briefs_data['campaign_briefs']),
    }
}

print("🎬 Testing visual_creator Agent with NEW OpenAI API Key")
print("=" * 70)
print()
print("📤 Triggering: data_ingest → campaign_strategist → visual_creator")
print()
print("📋 Test Data:")
print(f"  • Campaign Briefs: {len(briefs_data['campaign_briefs'])}")
print(f"  • Property Photos: {len(property_data['photos'])}")
print(f"  • Amenities: {len(property_data['amenities']['community'])}")
print(f"  • Local Amenities: {len(property_data['local_amenities']['walkable_distance'].keys())} categories")
print()
print("⏳ Sending request...")
print("-" * 70)

try:
    response = requests.post(API_URL, json=payload, headers=HEADERS, timeout=30)
    response.raise_for_status()
    
    result = response.json()
    
    print(f"\n✅ SUCCESS! Status Code: {response.status_code}")
    print(f"\nResponse:")
    print(json.dumps(result, indent=2))
    
    if 'session_id' in result:
        session_id = result['session_id']
        print(f"\n" + "=" * 70)
        print(f"📌 Session ID: {session_id}")
        print()
        print("🔍 What's happening:")
        print("   1. data_ingest processes property data")
        print("   2. campaign_strategist creates campaign briefs (using GPT-4o-mini)")
        print("   3. visual_creator generates visual packages IN PARALLEL (using GPT-4o)")
        print("   4. copywriter generates ad copy IN PARALLEL (using GPT-4o-mini)")
        print("   5. Both feed into human_approval for final review")
        print()
        print("📊 Check server logs to see:")
        print("   • Campaign strategist output")
        print("   • Visual creator video scripts & carousel designs")
        print("   • Copywriter ad copy variants")
        print()
        print("💾 Results are stored in the session for later retrieval")
        print("=" * 70)
    
except requests.exceptions.ConnectionError:
    print(f"❌ ERROR: Cannot connect to {API_URL}")
    print(f"   Make sure the server is running: python3 main.py")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    print(f"\nResponse: {response.text if 'response' in locals() else 'N/A'}")
    sys.exit(1)
