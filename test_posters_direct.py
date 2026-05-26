#!/usr/bin/env python3
"""
Direct visual_creator test - demonstrates poster generation capability
Bypasses the entire pipeline and calls visual_creator directly
"""
import asyncio
import sys
import json

# Import visual_creator directly
sys.path.insert(0, '/Users/bhumkamehndiratta/Desktop/Leafcraft/NewSocialMedia/SocialMediaMarketing_v2')
from agency.visual_creator_agent import visual_creator

# Test data
campaign_briefs = [
    {
        "brief_id": "brief_001",
        "renter_persona": "family",
        "target_floorplan": "2-Bedroom",
        "emotional_lever": "move_in_ease",
        "messaging_direction": "Emphasize quick approval and family amenities",
        "budget_allocation": 600,
        "platform_priority": ["meta_ads", "instagram_organic"],
    },
    {
        "brief_id": "brief_002",
        "renter_persona": "young_professional",
        "target_floorplan": "1-Bedroom",
        "emotional_lever": "convenience",
        "messaging_direction": "Highlight walkability and modern lifestyle",
        "budget_allocation": 550,
        "platform_priority": ["instagram_organic", "tiktok"],
    },
    {
        "brief_id": "brief_003",
        "renter_persona": "budget_conscious",
        "target_floorplan": "Studio",
        "emotional_lever": "affordability",
        "messaging_direction": "Focus on value and accessible pricing",
        "budget_allocation": 350,
        "platform_priority": ["craigslist", "zumper"],
    }
]

property_photos = [
    {"url": "photo1.jpg", "caption": "Luxury lobby", "tags": ["lobby", "modern"]},
    {"url": "photo2.jpg", "caption": "Modern kitchen", "tags": ["kitchen", "amenity"]},
    {"url": "photo3.jpg", "caption": "Fitness center", "tags": ["gym", "amenity"]},
    {"url": "photo4.jpg", "caption": "Pool area", "tags": ["pool", "outdoor"]},
    {"url": "photo5.jpg", "caption": "Community lounge", "tags": ["community", "social"]},
]

amenities = [
    "Swimming pool",
    "Fitness center",
    "Dog park",
    "Community room",
    "Rooftop lounge",
    "Concierge",
    "24-hour security",
    "Reserved parking",
    "Package room",
    "Bike storage"
]

async def test_visual_creator():
    print("🎨 DIRECT VISUAL CREATOR TEST")
    print("=" * 80)
    print()
    print("Input Data:")
    print(f"  • Campaign Briefs: {len(campaign_briefs)}")
    print(f"  • Property Photos: {len(property_photos)}")
    print(f"  • Amenities: {len(amenities)}")
    print()
    
    # Prepare input data
    input_data = {
        "campaign_briefs": json.dumps(campaign_briefs),
        "briefs_count": len(campaign_briefs),
        "property_photos": json.dumps(property_photos),
        "amenity_list": json.dumps(amenities),
        "occupancy_rate": 0.885,
        "priority_floorplans": json.dumps(["2-Bedroom", "1-Bedroom"]),
        "local_amenities": json.dumps({"walkable_distance": {"restaurants": 5, "parks": 3}}),
    }
    
    # Call visual_creator
    print("⏳ Calling visual_creator agent...\n")
    result = await visual_creator(None, input_data, {})
    
    # Display results
    print("✨ VISUAL CREATOR OUTPUT:\n")
    
    # Show poster designs
    if result.get('visual_packages'):
        posters = json.loads(result['visual_packages'])
        print("📐 POSTER DESIGNS:")
        for poster in posters:
            print()
            print(f"  🎨 {poster['name']}")
            print(f"     ├─ Persona: {poster['target_persona']}")
            print(f"     ├─ Floorplan: {poster['target_floorplan']}")
            print(f"     ├─ Lever: {poster['emotional_lever']}")
            print(f"     ├─ Headline: \"{poster['headline']}\"")
            print(f"     ├─ Subheadline: \"{poster['subheadline']}\"")
            print(f"     ├─ CTA: \"{poster['call_to_action']}\"")
            print(f"     ├─ Colors: {' → '.join(poster['color_palette'])}")
            print(f"     └─ Dimensions:")
            for format_name, dims in poster['dimensions'].items():
                print(f"        • {format_name}: {dims}")
    
    # Show carousel designs
    if result.get('carousel_structures'):
        carousels = json.loads(result['carousel_structures'])
        print(f"\n\n📑 CAROUSEL DESIGNS ({len(carousels)} sets):")
        for carousel in carousels:
            print()
            print(f"  📸 {carousel['carousel_id']}")
            print(f"     ├─ Platform: {carousel['platform']}")
            print(f"     ├─ Slides: {carousel['slide_count']}")
            print(f"     ├─ Aesthetic: {carousel['aesthetic']}")
            print(f"     └─ Slide Order:")
            for slide in carousel['slides']:
                print(f"        {slide['slide']}. {slide['content_type']}: \"{slide['copy']}\"")
    
    # Show video scripts
    if result.get('video_script_details'):
        scripts = json.loads(result['video_script_details'])
        print(f"\n\n🎬 VIDEO SCRIPTS ({len(scripts)} videos):")
        for script in scripts:
            print()
            print(f"  🎥 {script['title']}")
            print(f"     ├─ Duration: {script['duration_seconds']}s")
            print(f"     ├─ Persona: {script['persona']}")
            print(f"     └─ Scenes:")
            for scene in script['scene_breakdown']:
                print(f"        {scene['time']}: {scene['visual']}")
    
    # Summary
    print(f"\n\n📊 GENERATION SUMMARY:")
    print(f"   ✓ Posters: {result.get('briefs_covered', 0)}")
    print(f"   ✓ Carousel Sets: {result.get('carousel_count', 0)}")
    print(f"   ✓ Video Scripts: {result.get('video_scripts_count', 0)}")
    print(f"   ✓ Formats Produced: {json.loads(result.get('formats_produced', '[]'))}")
    
    print("\n" + "=" * 80)
    print("✅ POSTER GENERATION COMPLETE!")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    asyncio.run(test_visual_creator())
