#!/usr/bin/env python3
"""
Export generated posters to JSON files for viewing and storage
"""
import asyncio
import json
import sys
from pathlib import Path

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
]

amenities = [
    "Swimming pool", "Fitness center", "Dog park", "Community room",
    "Rooftop lounge", "Concierge", "24-hour security", "Reserved parking",
    "Package room", "Bike storage"
]

async def export_posters():
    print("📊 EXPORTING POSTERS TO JSON FILES\n")
    
    # Generate posters
    input_data = {
        "campaign_briefs": json.dumps(campaign_briefs),
        "briefs_count": len(campaign_briefs),
        "property_photos": json.dumps(property_photos),
        "amenity_list": json.dumps(amenities),
        "occupancy_rate": 0.885,
        "priority_floorplans": json.dumps(["2-Bedroom", "1-Bedroom"]),
        "local_amenities": json.dumps({"walkable_distance": {"restaurants": 5, "parks": 3}}),
    }
    
    result = await visual_creator(None, input_data, {})
    
    # Create output directory
    output_dir = Path('/Users/bhumkamehndiratta/Desktop/Leafcraft/NewSocialMedia/SocialMediaMarketing_v2/generated_posters')
    output_dir.mkdir(exist_ok=True)
    
    # Save poster designs
    posters = json.loads(result['visual_packages'])
    posters_file = output_dir / 'poster_designs.json'
    with open(posters_file, 'w') as f:
        json.dump(posters, f, indent=2)
    print(f"✅ Posters saved to: {posters_file}")
    
    # Save carousel designs
    carousels = json.loads(result['carousel_structures'])
    carousels_file = output_dir / 'carousel_designs.json'
    with open(carousels_file, 'w') as f:
        json.dump(carousels, f, indent=2)
    print(f"✅ Carousels saved to: {carousels_file}")
    
    # Save video scripts
    scripts = json.loads(result['video_script_details'])
    scripts_file = output_dir / 'video_scripts.json'
    with open(scripts_file, 'w') as f:
        json.dump(scripts, f, indent=2)
    print(f"✅ Video scripts saved to: {scripts_file}")
    
    # Save complete package
    complete = {
        "metadata": {
            "generated_at": "2026-05-26",
            "property": "Riverside Luxury Apartments",
            "campaigns": len(posters),
        },
        "posters": posters,
        "carousels": carousels,
        "video_scripts": scripts,
        "summary": result
    }
    
    complete_file = output_dir / 'complete_poster_package.json'
    with open(complete_file, 'w') as f:
        json.dump(complete, f, indent=2)
    print(f"✅ Complete package saved to: {complete_file}")
    
    print(f"\n📂 All files saved to: {output_dir}")
    print(f"\n📋 Files created:")
    print(f"   • poster_designs.json - Design specs for all 3 posters")
    print(f"   • carousel_designs.json - Carousel slide structures")
    print(f"   • video_scripts.json - Video scripts with scene breakdowns")
    print(f"   • complete_poster_package.json - Everything in one file")

if __name__ == "__main__":
    asyncio.run(export_posters())
