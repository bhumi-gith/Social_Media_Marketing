#!/usr/bin/env python3
"""
Test the new visual_creator with HTML-based poster design and PNG export
"""
import asyncio
import sys
import json
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

async def test_new_visual_creator():
    print("🎨 NEW VISUAL CREATOR TEST - HTML + PNG POSTERS")
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
    print("\n✨ VISUAL CREATOR OUTPUT:\n")
    
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
            print(f"     ├─ Ratios: {', '.join(poster['ratios_generated'])}")
            print(f"     └─ Files Created:")
            for file_path in poster['files_created']:
                file_name = Path(file_path).name
                status = "✓" if Path(file_path).exists() else "✗"
                print(f"        {status} {file_name}")
    
    # Summary
    print(f"\n\n📊 GENERATION SUMMARY:")
    print(f"   ✓ Briefs Covered: {result.get('briefs_covered', 0)}")
    print(f"   ✓ Formats Produced: {json.loads(result.get('formats_produced', '[]'))}")
    print(f"   ✓ Total Files Saved: {result.get('poster_files_saved', 0)}")
    
    # List generated files
    output_dir = Path('/Users/bhumkamehndiratta/Desktop/Leafcraft/NewSocialMedia/SocialMediaMarketing_v2/generated_posters')
    if output_dir.exists():
        print(f"\n📁 Files in {output_dir.name}:")
        html_files = list(output_dir.glob('*.html'))
        png_files = list(output_dir.glob('*.png'))
        
        if html_files:
            print(f"\n   HTML Files ({len(html_files)}):")
            for f in sorted(html_files):
                print(f"      • {f.name}")
        
        if png_files:
            print(f"\n   PNG Files ({len(png_files)}):")
            for f in sorted(png_files):
                size_kb = f.stat().st_size / 1024
                print(f"      • {f.name} ({size_kb:.1f} KB)")
        
        if not html_files and not png_files:
            print("      (No files generated yet)")
    
    print("\n" + "=" * 80)
    print("✅ POSTER GENERATION COMPLETE!")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    asyncio.run(test_new_visual_creator())
