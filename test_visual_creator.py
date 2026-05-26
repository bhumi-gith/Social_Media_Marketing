#!/usr/bin/env python3
"""
Test visual_creator agent by triggering the full workflow
"""
import json
import requests
import sys

API_URL = "http://127.0.0.1:18820/api/mesh/request"
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": "test"
}

# Read test data
with open('tests/test_property_data.json', 'r') as f:
    property_data = json.load(f)

# Prepare payload for data_ingest agent
payload = {
    "entry_point": "marketing_pipeline",
    "data": {
        "vacancy_by_floorplan": json.dumps({
            k: f"{v['occupancy_rate']*100:.1f}% occupancy ({v['units_available']} units)"
            for k, v in property_data['vacancy_data'].items()
        }),
        "current_pricing": json.dumps(property_data['pricing']),
        "active_concessions": json.dumps(property_data['active_concessions']),
        "occupancy_rate": property_data['overall_occupancy'],
        "priority_floorplans": json.dumps([p['floorplan'] for p in property_data['priority_floorplans']]),
        "local_amenities": json.dumps(property_data['local_amenities']),
        "property_photos": json.dumps(property_data['photos']),
        "amenity_list": json.dumps(property_data['amenities']['community'])
    }
}

print("🚀 Testing LeafMesh Workflow: visual_creator Agent")
print("=" * 60)
print(f"\n📤 Endpoint: {API_URL}")
print(f"📌 Entry Point: marketing_pipeline")
print(f"\n📋 Payload Summary:")
print(f"  - Occupancy: {property_data['overall_occupancy']*100:.1f}%")
print(f"  - Priority Floorplans: {', '.join([p['floorplan'] for p in property_data['priority_floorplans']])}")
print(f"  - Active Concessions: {len(property_data['active_concessions'])} offer(s)")
print(f"  - Photos Available: {len(property_data['photos'])} images")
print(f"  - Amenities: {len(property_data['amenities']['community'])} available")

print(f"\n⏳ Sending request to LeafMesh...")
print("-" * 60)

try:
    response = requests.post(API_URL, json=payload, headers=HEADERS, timeout=30)
    response.raise_for_status()
    
    result = response.json()
    
    print(f"\n✅ SUCCESS! Status Code: {response.status_code}")
    print(f"\n📋 Response:")
    print(json.dumps(result, indent=2)[:1000])
    
    if 'session_id' in result:
        print(f"\n📌 Session ID: {result['session_id']}")
        print(f"   Use this to track workflow execution and view results")
    
    print(f"\n🔍 Next Steps:")
    print(f"   1. Watch the server logs for agent execution")
    print(f"   2. Visual Creator should generate visual packages")
    print(f"   3. Copywriter will generate ad copy variants")
    print(f"   4. Both feed into human_approval agent")
    
except requests.exceptions.ConnectionError:
    print(f"❌ ERROR: Cannot connect to {API_URL}")
    print(f"   Make sure the server is running: python3 main.py")
    sys.exit(1)
    
except requests.exceptions.Timeout:
    print(f"⏱️  Request timed out after 30 seconds")
    print(f"   The workflow may still be processing...")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)
