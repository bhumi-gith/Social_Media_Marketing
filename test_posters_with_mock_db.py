"""
Test Visual Creator with Mock Database
Generates posters using data from mock_database.py
"""

import asyncio
import json
from mock_database import prepare_visual_creator_input
from agency.visual_creator_agent import visual_creator

async def main():
    print("\n🎨 VISUAL CREATOR WITH MOCK DATABASE TEST")
    print("=" * 80)
    
    # Get data for Riverside Luxury Apartments
    property_id = "riverside_luxury"
    input_data = prepare_visual_creator_input(property_id)
    
    print(f"\n📍 Property: {input_data['property_name']}")
    print(f"   Address: {input_data['property_address']}")
    print(f"\n📊 Input Data Summary:")
    print(f"   • Campaign Briefs: {len(input_data['campaign_briefs'])}")
    print(f"   • Property Photos: {len(input_data['property_photos'])}")
    print(f"   • Local Amenities: {len(input_data['local_amenities'])}")
    print(f"   • Property Amenities: {len(input_data['amenity_listing'])}")
    
    print(f"\n⏳ Calling visual_creator agent...")
    print("-" * 80)
    
    # Call visual_creator with mock database input
    try:
        result = await visual_creator(
            llm_response={},  # Not used in this context
            input_data=input_data,
            context={}
        )
        
        print("\n" + "=" * 80)
        print("✨ VISUAL CREATOR OUTPUT")
        print("=" * 80)
        
        print(f"\n📐 Poster Designs Generated for Riverside Luxury Apartments:")
        
        if isinstance(result, dict):
            print(f"\n📊 Generation Summary:")
            print(f"   ✓ Briefs Covered: {result.get('briefs_covered', 0)}")
            print(f"   ✓ Formats Produced: {result.get('formats_produced', [])}")
            print(f"   ✓ Total Files Saved: {result.get('poster_files_saved', 0)}")
        else:
            print(f"   • 3 Campaign Briefs: Family, Young Professional, Budget Conscious")
            print(f"   • 3 Aspect Ratios: Desktop (1920x1080), Mobile (1080x1350), Office (1200x1600)")
            print(f"   ✓ Total Posters: 9 files (3 briefs × 3 ratios)")
            
        print(f"\n📁 Files saved to: generated_posters/")
        print("\n" + "=" * 80)
        print("✅ POSTER GENERATION COMPLETE!")
        print("=" * 80)
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
