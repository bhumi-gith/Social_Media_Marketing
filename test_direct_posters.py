#!/usr/bin/env python3
"""
Direct poster generation bypassing the full pipeline
Calls visual_creator directly with campaign briefs
"""
import json
import requests
import time
import sys

API_URL = "http://127.0.0.1:18820/api/mesh/request"
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": "test"
}

# Load campaign briefs
with open('tests/test_campaign_briefs.json', 'r') as f:
    briefs_data = json.load(f)

# Load property data
with open('tests/test_property_data.json', 'r') as f:
    property_data = json.load(f)

# Create a request that triggers visual_creator directly
# This simulates campaign_strategist having already run
payload = {
    "entry_point": "marketing_pipeline",
    "data": {
        # Include the campaign briefs that would come from strategist
        "campaign_briefs": json.dumps(briefs_data['campaign_briefs']),
        "briefs_count": len(briefs_data['campaign_briefs']),
        "total_budget_allocated": sum(b.get('budget_allocation', 0) for b in briefs_data['campaign_briefs']),
        
        # Include property data for context
        "vacancy_by_floorplan": json.dumps(property_data.get('vacancy_data', {})),
        "current_pricing": json.dumps({
            k: v.get('avg_rent', 0) 
            for k, v in property_data.get('vacancy_data', {}).items()
        }),
        "occupancy_rate": property_data.get('overall_occupancy', 0.88),
        "property_photos": json.dumps(property_data.get('photos', [])),
        "amenity_list": json.dumps(property_data.get('amenities', {}).get('community', [])),
    }
}

print("🎨 DIRECT POSTER GENERATION")
print("=" * 80)
print()
print("🎯 Campaign Briefs:")
for i, brief in enumerate(briefs_data['campaign_briefs'], 1):
    print(f"  {i}. {brief['renter_persona'].title()}")
    print(f"     ├─ Target: {brief['target_floorplan']}")
    print(f"     ├─ Lever: {brief['emotional_lever']}")
    print(f"     ├─ Budget: ${brief['budget_allocation']}")
    print(f"     └─ Platforms: {', '.join(brief['platform_priority'][:2])}")
print()

print("📸 Property Context:")
print(f"  • {len(property_data.get('photos', []))} photos available")
print(f"  • {len(property_data.get('amenities', {}).get('community', []))} amenities")
print(f"  • Occupancy: {property_data.get('overall_occupancy', 0.88):.1%}")
print()

print("-" * 80)
print("⏳ Submitting poster generation request...\n")

try:
    response = requests.post(API_URL, json=payload, headers=HEADERS, timeout=30)
    response.raise_for_status()
    
    result = response.json()
    session_id = result['session_id']
    
    print(f"✅ Request submitted!")
    print(f"\n📌 Session ID: {session_id}")
    print(f"\n⏳ Agents are generating posters now...")
    print()
    
    # Poll for results
    max_attempts = 30
    for attempt in range(1, max_attempts + 1):
        time.sleep(2)
        
        session_response = requests.get(
            f"http://127.0.0.1:18820/api/sessions/{session_id}",
            headers=HEADERS,
            timeout=10
        )
        
        if session_response.status_code == 200:
            session_data = session_response.json()
            state = session_data.get('state', {})
            
            # Check for visual_creator output
            if 'visual_creator_yields' in state:
                print(f"\n✨ POSTERS GENERATED! ({attempt * 2}s elapsed)")
                print()
                print("=" * 80)
                
                yields = state['visual_creator_yields']
                
                if yields:
                    print("\n📐 POSTER DESIGN SPECIFICATIONS:")
                    print()
                    
                    for key, value in yields.items():
                        if value and value not in ['{}', '[]', '']:
                            print(f"  📌 {key.replace('_', ' ').title()}:")
                            try:
                                parsed = json.loads(value) if isinstance(value, str) else value
                                if isinstance(parsed, list):
                                    print(f"     Items: {len(parsed)}")
                                    if len(parsed) > 0:
                                        print(f"     Sample: {json.dumps(parsed[0], indent=8)[:200]}...")
                                else:
                                    print(f"     {json.dumps(parsed)[:300]}...")
                            except:
                                print(f"     {str(value)[:200]}...")
                            print()
                
                print("=" * 80)
                print()
                print("🎉 Poster generation complete!")
                break
        
        if attempt % 5 == 0:
            print(f"   ⏳ Still working... ({attempt * 2}s)")
    else:
        print(f"\n⏱️ Poster generation is processing in background")
        print(f"   Check back with session ID: {session_id}")

except Exception as e:
    print(f"❌ ERROR: {e}")
    if 'response' in locals():
        print(f"Response: {response.text}")
    sys.exit(1)
