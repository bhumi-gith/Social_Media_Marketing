#!/usr/bin/env python3
"""
Generate marketing posters using visual_creator agent
Calls visual_creator directly with campaign briefs and property data
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

# Load test data
with open('tests/test_campaign_briefs.json', 'r') as f:
    briefs_data = json.load(f)

with open('tests/test_property_data.json', 'r') as f:
    property_data = json.load(f)

# Create a specialized poster generation request
poster_request = {
    "entry_point": "marketing_pipeline",
    "data": {
        # Property context
        "vacancy_by_floorplan": json.dumps(property_data['vacancy_data']),
        "current_pricing": json.dumps({k: v.get('avg_rent', 0) for k, v in property_data['vacancy_data'].items()}),
        "active_concessions": json.dumps(property_data.get('active_concessions', [])),
        "occupancy_rate": property_data['overall_occupancy'],
        "priority_floorplans": json.dumps([p['floorplan'] for p in property_data['priority_floorplans']]),
        "local_amenities": json.dumps(property_data.get('local_amenities', {})),
        "property_photos": json.dumps(property_data.get('photos', [])),
        "amenity_list": json.dumps(property_data.get('amenities', {}).get('community', [])),
        
        # Campaign briefs for visual_creator
        "campaign_briefs": json.dumps(briefs_data['campaign_briefs']),
        "briefs_count": len(briefs_data['campaign_briefs']),
        
        # Explicit poster request (visual_creator will see this context)
        "creative_focus": "posters",
        "poster_types": json.dumps([
            "leasing_office_displays",
            "digital_signage", 
            "social_media_static_posts",
            "email_banner_ads"
        ])
    }
}

print("🎨 POSTER GENERATION TEST")
print("=" * 80)
print()
print("📋 Generating posters for:")
print()

for i, brief in enumerate(briefs_data['campaign_briefs'], 1):
    print(f"  {i}. {brief['renter_persona'].title()} - {brief['target_floorplan']}")
    print(f"     Lever: {brief['emotional_lever']}")
    print(f"     Budget: ${brief['budget_allocation']}")
    print()

print("🎯 Poster Types:")
print("  • Leasing office displays")
print("  • Digital signage (screens at property)")
print("  • Social media posts (Instagram, Facebook)")
print("  • Email banner ads")
print()
print("-" * 80)
print("⏳ Sending request to visual_creator agent...")
print()

try:
    response = requests.post(API_URL, json=poster_request, headers=HEADERS, timeout=30)
    response.raise_for_status()
    
    result = response.json()
    
    print(f"✅ Request submitted successfully!")
    print(f"\n📌 Session ID: {result['session_id']}")
    print()
    print("🔄 Agent Processing:")
    print("   1. visual_creator is analyzing campaign briefs")
    print("   2. Creating poster designs for each persona")
    print("   3. Optimizing visuals for each channel")
    print("   4. Generating design specifications")
    print()
    print("⏱️  Waiting for visual_creator to complete...")
    print()
    
    # Wait and check for results
    session_id = result['session_id']
    max_attempts = 15
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        time.sleep(2)
        
        # Check session status
        session_response = requests.get(
            f"http://127.0.0.1:18820/api/sessions/{session_id}",
            headers=HEADERS,
            timeout=10
        )
        
        if session_response.status_code == 200:
            session_data = session_response.json()
            
            # Check if visual_creator has produced output
            if 'state' in session_data and 'visual_creator_yields' in session_data['state']:
                yields = session_data['state']['visual_creator_yields']
                
                print(f"✨ VISUAL CREATOR OUTPUT RECEIVED!")
                print()
                print("=" * 80)
                print()
                
                # Parse and display the yields
                output_keys = [k for k in yields.keys() if yields[k] and yields[k] != '[]' and yields[k] != '{}']
                
                if output_keys:
                    print("📊 Generated Poster Specifications:")
                    print()
                    
                    for key in output_keys:
                        value = yields[key]
                        print(f"  📌 {key.replace('_', ' ').title()}:")
                        
                        # Try to parse as JSON for prettier output
                        try:
                            parsed = json.loads(value) if isinstance(value, str) else value
                            if isinstance(parsed, list) and len(parsed) > 0:
                                for item in parsed[:2]:  # Show first 2 items
                                    print(f"     • {json.dumps(item, indent=8)}")
                                if len(parsed) > 2:
                                    print(f"     ... and {len(parsed) - 2} more")
                            else:
                                print(f"     {json.dumps(parsed, indent=8)}")
                        except:
                            print(f"     {value[:200]}...")
                        print()
                
                print("=" * 80)
                print()
                print("✅ Poster generation complete!")
                print()
                print("📊 Design Details Generated:")
                print("   • Color palettes and visual themes")
                print("   • Typography recommendations")
                print("   • Image selections from property photos")
                print("   • Headline copy for each persona")
                print("   • Call-to-action recommendations")
                print("   • Sizing specs for each channel")
                print()
                break
        
        if attempt % 3 == 0:
            print(f"   ⏳ Checking... ({attempt * 2}s elapsed)")
    
    if attempt >= max_attempts:
        print("⏱️ Request still processing...")
        print(f"   Session will continue in the background.")
        print(f"   Check back with session ID: {session_id}")
    
except requests.exceptions.ConnectionError:
    print(f"❌ ERROR: Cannot connect to http://127.0.0.1:18820")
    print(f"   Make sure the server is running: python3 main.py")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    if 'response' in locals():
        print(f"\nResponse: {response.text}")
    sys.exit(1)
