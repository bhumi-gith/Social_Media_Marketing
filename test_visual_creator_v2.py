#!/usr/bin/env python3
"""
Direct test for the updated visual_creator agent (v2).
Calls the agent function without the LeafMesh server.
"""
import asyncio
import json
import sys

sys.path.insert(0, '/Users/bhumkamehndiratta/Desktop/Leafcraft/NewSocialMedia/SocialMediaMarketing_v2')
from agency.visual_creator_agent import visual_creator

# ── Test data ──────────────────────────────────────────────────────────────────

CAMPAIGN_BRIEFS = [
    {
        "brief_id": "brief_001",
        "renter_persona": "family",
        "target_floorplan": "2-Bedroom",
        "emotional_lever": "move_in_ease",
        "messaging_direction": "Hassle-free move-in for families. Quick 24-hr approval, move-in this weekend.",
        "key_selling_points": [
            "Approved in 24 hours",
            "3 min from Riverside Park & playground",
            "5 min to Lincoln Elementary (rated 8.5/10)"
        ],
        "headlines": ["Move In This Weekend — Zero Stress", "Approved in 24 Hours. Home by Friday."],
        "concession_flag": True,
        "concession_details": "Waived deposit + $100 move-in credit",
        "budget_allocation": 600,
        "platform_priority": ["meta_ads", "instagram_organic", "craigslist"],
    },
    {
        "brief_id": "brief_002",
        "renter_persona": "young_professional",
        "target_floorplan": "1-Bedroom",
        "emotional_lever": "convenience",
        "messaging_direction": "Walk to coffee, work hubs, nightlife. 10-min commute to tech district.",
        "key_selling_points": [
            "10 min to Denver Tech District",
            "Walk to Blue Bottle Coffee (2 min)",
            "Metro Station 4 min away"
        ],
        "headlines": ["Walk to Everything. Work Anywhere.", "Live 10 Minutes From Everything."],
        "concession_flag": False,
        "budget_allocation": 550,
        "platform_priority": ["instagram_organic", "tiktok", "meta_ads"],
    },
    {
        "brief_id": "brief_003",
        "renter_persona": "budget_conscious",
        "target_floorplan": "Studio",
        "emotional_lever": "affordability",
        "messaging_direction": "Luxury finishes at studio rates. $1,150/mo vs competitors $1,300+.",
        "key_selling_points": [
            "$1,150/mo — $150 below market",
            "Quartz countertops & stainless steel",
            "Pool + dog park included"
        ],
        "headlines": ["Luxury Finishes. Honest Price.", "$1,150/mo — Less Than You Think."],
        "concession_flag": True,
        "concession_details": "Waived deposit ($0 move-in)",
        "budget_allocation": 350,
        "platform_priority": ["craigslist", "zumper", "facebook"],
    },
]

# Real Unsplash images (public CDN)
PROPERTY_PHOTOS = [
    {
        "url": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=1280&q=80",
        "caption": "EXTERIOR",
        "tags": ["exterior", "building"],
    },
    {
        "url": "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=800&q=80",
        "caption": "KITCHEN",
        "tags": ["kitchen", "unit"],
    },
    {
        "url": "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800&q=80",
        "caption": "LIVING ROOM",
        "tags": ["living", "unit"],
    },
    {
        "url": "https://images.unsplash.com/photo-1540518614846-7eded433c457?w=800&q=80",
        "caption": "BEDROOM",
        "tags": ["bedroom", "unit"],
    },
    {
        "url": "https://images.unsplash.com/photo-1575429198097-0414ec08e8cd?w=800&q=80",
        "caption": "POOL",
        "tags": ["pool", "amenity"],
    },
]

PRICING = {
    "studio":        "$1,150/mo",
    "one_bedroom":   "$1,650/mo",
    "two_bedroom":   "$2,050/mo",
    "three_bedroom": "$2,800/mo",
}

AMENITIES = [
    "Resort-style heated pool",
    "24/7 fitness center",
    "Pet-friendly dog park",
    "Co-working lounge with WiFi",
    "Rooftop terrace with city views",
    "Movie theater room",
    "EV charging stations",
    "Concierge service 24/7",
]

# Mock LLM response: each brief picks template 1-3 within its lever's set
# brief_001: move_in_ease  T3 → Blue Hero Poster (bold primary-bg headline + photos + checkmarks)
# brief_002: convenience   T1 → Split Urban      (image-forward urban layout)
# brief_003: affordability T3 → Blue Hero Poster (price clarity with MONTHLY RENT card prominent)
MOCK_LLM_RESPONSE = json.dumps({
    "template_selections": [
        {
            "brief_id": "brief_001",
            "template_number": 3,
            "reasoning": "Blue Hero Poster's bold primary-bg headline and checkmark features make move-in clarity unmistakable for families"
        },
        {
            "brief_id": "brief_002",
            "template_number": 1,
            "reasoning": "Split Urban's image-forward layout suits the urban convenience narrative for young professionals"
        },
        {
            "brief_id": "brief_003",
            "template_number": 3,
            "reasoning": "Blue Hero Poster puts MONTHLY RENT front and center — maximum price clarity for budget-conscious renters"
        },
    ]
})

# ── Runner ─────────────────────────────────────────────────────────────────────

async def run():
    print("🎨  Visual Creator v2 — Direct Test")
    print("=" * 72)
    print(f"  Briefs  : {len(CAMPAIGN_BRIEFS)}")
    print(f"  Photos  : {len(PROPERTY_PHOTOS)}")
    print(f"  Templates assigned: move_in_ease→T3 (Blue Hero), convenience→T1 (Split Urban), affordability→T3 (Blue Hero)")
    print()

    input_data = {
        "campaign_briefs":  json.dumps(CAMPAIGN_BRIEFS),
        "property_photos":  json.dumps(PROPERTY_PHOTOS),
        "amenity_list":     json.dumps(AMENITIES),
        "current_pricing":  json.dumps(PRICING),
        "sq_footage_map":   json.dumps({
            "studio":        "520 sq ft",
            "one_bedroom":   "780 sq ft",
            "two_bedroom":   "1,080 sq ft",
            "three_bedroom": "1,420 sq ft",
        }),
        "contact_phone":    "(720) 555-0198",
        "contact_website":  "www.riversideluxury.com",
        "contact_address":  "2150 Riverside Blvd, Denver CO 80202",
        "property_name":    "Riverside Luxury",
        "availability":     "For Rent",
    }

    print("⏳  Generating posters …\n")
    result = await visual_creator(MOCK_LLM_RESPONSE, input_data, {})

    # ── Report ─────────────────────────────────────────────────────────────────
    posters = json.loads(result.get("visual_packages", "[]"))

    print(f"{'─' * 72}")
    print(f"  RESULT: {result['briefs_covered']} poster sets  |  "
          f"{result['poster_files_saved']} PNGs saved")
    print(f"{'─' * 72}\n")

    for p in posters:
        print(f"  📋  {p['name']}  (template {p['template_used']})")
        print(f"      Lever     : {p['emotional_lever']}")
        print(f"      Headline  : {p['headline']}")
        print(f"      Subhead   : {p['subheadline'][:70]}…")
        print(f"      Price     : {p['pricing_info']}")
        print(f"      CTA       : {p['call_to_action']}")
        print(f"      Rooms     : {', '.join(r['label'] for r in p['room_photos'])}")
        print(f"      Files     : {len(p['files_created'])} ({', '.join(f.split('/')[-1] for f in p['files_created'][:2])} …)")
        print()

    print("=" * 72)
    print("✅  Done — open generated_posters/ to view the HTML/PNG files.")
    print("=" * 72)

if __name__ == "__main__":
    asyncio.run(run())
