"""
Generate Campaign Briefs using Campaign Strategist Agent
Tests the new real estate marketing framework with mock database
"""

import asyncio
import json
from campaign_strategist_mock_data import get_campaign_strategist_input

async def generate_campaign_briefs(property_id: str):
    """Generate campaign briefs for a property using LLM"""
    
    print("\n" + "="*80)
    print("🎯 CAMPAIGN STRATEGIST - GENERATE BRIEFS")
    print("="*80)
    
    # Load mock data
    input_data = get_campaign_strategist_input(property_id)
    
    if not input_data:
        print(f"❌ Property {property_id} not found")
        return
    
    print(f"\n📍 Property: {input_data['property_name']}")
    print(f"   Address: {input_data['property_address']}")
    
    # Display key metrics
    print(f"\n📊 Market Snapshot:")
    print(f"   • Occupancy Rate: {input_data['occupancy_rate']}%")
    print(f"   • Priority Floorplans: {', '.join(input_data['priority_floorplans'])}")
    print(f"   • Concession Triggered: {'✅ YES' if input_data['concession_triggered'] else '❌ NO'}")
    
    print(f"\n💰 Vacancy by Floorplan:")
    for fp, vacancy in input_data['vacancy_by_floorplan'].items():
        print(f"   • {fp}: {vacancy}")
    
    print(f"\n💵 Current Pricing:")
    for fp, price in input_data['current_pricing'].items():
        print(f"   • {fp}: ${price}/month")
    
    if input_data['active_concessions']:
        print(f"\n🎁 Active Concessions:")
        for conc in input_data['active_concessions']:
            print(f"   • {conc['name']}: {conc['description']} (${conc['value']} value)")
    
    print(f"\n🏆 Competitors:")
    for comp in input_data['competitor_report']['primary_competitors']:
        price = comp.get('avg_price_1bed') or comp.get('avg_price_3bed', 'N/A')
        print(f"   • {comp['name']}: ${price}/mo, {comp['occupancy']}% occupancy")
    
    print(f"\n🎯 Market Conditions:")
    mc = input_data['market_conditions']
    print(f"   • Economic Index: {mc['economic_index']}")
    print(f"   • Employment Growth: {mc['employment_growth']}%")
    print(f"   • Migration Trend: {mc['migration_trend']}")
    
    # Prepare data for LLM
    print(f"\n⏳ Calling Campaign Strategist Agent...")
    print("-"*80)
    
    # Import and call the agent directly
    try:
        from leafmesh import LeafMeshClient
        
        # Initialize LeafMesh client
        client = LeafMeshClient()
        
        # Prepare input for campaign_strategist
        agent_input = {
            "vacancy_by_floorplan": json.dumps(input_data['vacancy_by_floorplan']),
            "current_pricing": json.dumps(input_data['current_pricing']),
            "active_concessions": json.dumps(input_data['active_concessions']),
            "occupancy_rate": input_data['occupancy_rate'],
            "priority_floorplans": json.dumps(input_data['priority_floorplans']),
            "local_amenities": json.dumps(input_data['local_amenities']),
            "property_photos": json.dumps({"count": 5, "types": ["living", "kitchen", "bedroom", "amenities", "exterior"]}),
            "amenity_list": json.dumps(input_data['property_amenities']),
            "concession_triggered": input_data['concession_triggered'],
            "triggered_floorplans": json.dumps(input_data['triggered_floorplans']),
            "competitor_report": json.dumps(input_data['competitor_report']),
            "optimization_briefs": json.dumps(input_data['optimization_briefs'])
        }
        
        # Call agent
        result = await client.call_agent("campaign_strategist", agent_input)
        
        print("\n" + "="*80)
        print("✨ CAMPAIGN BRIEFS GENERATED")
        print("="*80)
        
        if result and isinstance(result, dict):
            # Parse campaign briefs
            briefs_data = result.get('campaign_briefs', '[]')
            if isinstance(briefs_data, str):
                try:
                    briefs = json.loads(briefs_data)
                except:
                    briefs = []
            else:
                briefs = briefs_data
            
            if isinstance(briefs, list):
                for i, brief in enumerate(briefs, 1):
                    print(f"\n📋 BRIEF {i}:")
                    print(f"   Target Floorplan: {brief.get('target_floorplan', 'N/A')}")
                    print(f"   Renter Persona: {brief.get('renter_persona', 'N/A')}")
                    print(f"   Emotional Lever: {brief.get('emotional_lever', 'N/A')}")
                    
                    if 'headlines' in brief:
                        print(f"   Proposed Headlines:")
                        for headline in brief.get('headlines', [])[:3]:
                            print(f"      • {headline}")
                    
                    if 'key_selling_points' in brief:
                        print(f"   Key Selling Points:")
                        for point in brief.get('key_selling_points', [])[:3]:
                            print(f"      • {point}")
                    
                    print(f"   Budget Allocation: ${brief.get('budget_allocation', 0):,}")
                    print(f"   Platform Priority: {', '.join(brief.get('platform_priority', [])[:3])}")
                    
                    if brief.get('concession_message'):
                        print(f"   Concession Message: {brief.get('concession_message')}")
            
            # Summary
            print(f"\n📊 Summary:")
            print(f"   • Total Briefs: {result.get('briefs_count', 0)}")
            print(f"   • Total Budget: ${result.get('total_budget_allocated', 0):,}")
            print(f"   • Levers Used: {result.get('levers_used', 'N/A')}")
            print(f"   • Platforms: {result.get('platforms_targeted', 'N/A')}")
        
        print("\n" + "="*80)
        print("✅ CAMPAIGN BRIEF GENERATION COMPLETE")
        print("="*80)
        
    except ImportError:
        print("⚠️  LeafMesh client not available - displaying mock strategic analysis instead")
        print_strategic_analysis(input_data)
    except Exception as e:
        print(f"⚠️  Error calling agent: {e}")
        print("   Displaying mock strategic analysis instead...")
        print_strategic_analysis(input_data)


def print_strategic_analysis(data: dict):
    """Print strategic analysis based on mock data"""
    
    print("\n📊 STRATEGIC ANALYSIS (Based on Market Data):\n")
    
    # Identify target floorplans by vacancy
    vacancy = data['vacancy_by_floorplan']
    sorted_vacancies = sorted(vacancy.items(), key=lambda x: float(x[1].rstrip('%')), reverse=True)
    
    print("🎯 RECOMMENDED CAMPAIGN BRIEFS:\n")
    
    # Brief 1: Highest Vacancy
    if len(sorted_vacancies) > 0:
        fp1 = sorted_vacancies[0][0]
        print(f"BRIEF 1: {fp1.upper()}")
        print(f"   Vacancy: {sorted_vacancies[0][1]}")
        print(f"   Target Persona: young_professional")
        print(f"   Emotional Lever: convenience")
        print(f"   Sample Headline: 'Live Near Everything. Work From Anywhere.'")
        print(f"   Key Points:")
        for amenity in data['local_amenities'][:3]:
            print(f"      • {amenity}")
        print(f"   Budget: $40,000")
        print(f"   Platforms: Meta Ads, Instagram, Google Ads")
        
        if data['concession_triggered']:
            print(f"   Concession: Yes - Include limited-time offer")
        print()
    
    # Brief 2: Second Highest Vacancy or Different Persona
    if len(sorted_vacancies) > 1:
        fp2 = sorted_vacancies[1][0]
        print(f"BRIEF 2: {fp2.upper()}")
        print(f"   Vacancy: {sorted_vacancies[1][1]}")
        print(f"   Target Persona: family_with_kids")
        print(f"   Emotional Lever: family_safety")
        print(f"   Sample Headline: 'Space for Your Family. Safety You Can Trust.'")
        print(f"   Key Points:")
        for amenity in data['property_amenities'][:3]:
            print(f"      • {amenity}")
        print(f"   Budget: $35,000")
        print(f"   Platforms: Facebook, Nextdoor, Google Ads")
        print()
    
    # Brief 3: Alternative Strategy
    print(f"BRIEF 3: PREMIUM POSITIONING")
    print(f"   Target Persona: remote_worker")
    print(f"   Emotional Lever: affordability")
    print(f"   Sample Headline: 'All the Amenities. Smart Pricing.'")
    print(f"   Key Points:")
    for amenity in data['property_amenities'][3:6]:
        print(f"      • {amenity}")
    print(f"   Budget: $25,000")
    print(f"   Platforms: Instagram, TikTok, Craigslist")
    print()
    
    print("💰 BUDGET SUMMARY:")
    print(f"   Brief 1: $40,000")
    print(f"   Brief 2: $35,000")
    print(f"   Brief 3: $25,000")
    print(f"   TOTAL: $100,000")


async def main():
    # Generate briefs for all properties
    properties = [
        "riverside_luxury",
        "downtown_modern",
        "suburban_family"
    ]
    
    print("\n🚀 CAMPAIGN BRIEF GENERATION FOR ALL PROPERTIES")
    print("="*80)
    
    for prop_id in properties:
        await generate_campaign_briefs(prop_id)
        print("\n")


if __name__ == "__main__":
    asyncio.run(main())
