"""
Mock Database for Campaign Strategist Agent
Contains realistic real estate marketing data for Austin, TX properties
"""

CAMPAIGN_STRATEGIST_MOCK_DATA = {
    "properties": [
        {
            "id": "riverside_luxury",
            "name": "Riverside Luxury Apartments",
            "address": "123 Waterfront Drive, Austin, TX",
            "market_data": {
                "vacancy_by_floorplan": {
                    "studio": "2%",
                    "1bed": "3%",
                    "2bed": "4%",
                    "3bed": "6%"
                },
                "current_pricing": {
                    "studio": 1200,
                    "1bed": 1600,
                    "2bed": 2100,
                    "3bed": 2800
                },
                "active_concessions": [
                    {
                        "name": "Move-in Special",
                        "description": "50% off first month rent",
                        "floorplans": ["studio", "1bed"],
                        "value": 600,
                        "end_date": "2026-06-30"
                    },
                    {
                        "name": "Parking Waived",
                        "description": "Free parking for 3 months",
                        "floorplans": ["2bed", "3bed"],
                        "value": 225,
                        "end_date": "2026-07-15"
                    }
                ],
                "occupancy_rate": 94.2,
                "priority_floorplans": ["1bed", "2bed"],
                "local_amenities": [
                    "Downtown proximity (0.5 mi)",
                    "Top-rated restaurants (8)",
                    "Public transit hub",
                    "Riverside Park trail access",
                    "Tech campus nearby",
                    "Premium retail (3 centers)"
                ],
                "property_amenities": [
                    "Rooftop infinity pool with city views",
                    "24/7 fitness center with yoga studios",
                    "Co-working spaces with fiber internet",
                    "Pet spa and dog park",
                    "Theater room and game lounge",
                    "Concierge service"
                ],
                "concession_triggered": True,
                "triggered_floorplans": ["1bed"],
                "trigger_reason": "Low occupancy and seasonal demand",
                "competitor_report": {
                    "primary_competitors": [
                        {
                            "name": "Downtown Lofts",
                            "distance": "0.3 mi",
                            "avg_price_1bed": 1750,
                            "occupancy": 96,
                            "key_amenities": ["Co-working", "Gym", "Parking"]
                        },
                        {
                            "name": "Riverside Park Residences",
                            "distance": "0.2 mi",
                            "avg_price_1bed": 1550,
                            "occupancy": 98,
                            "key_amenities": ["Pet-friendly", "Pool", "Parking"]
                        }
                    ],
                    "market_trend": "Slight cooling in premium market",
                    "competitor_concessions": "Limited - mostly in 3bed+"
                },
                "optimization_briefs": [
                    {
                        "target_audience": "Young professionals",
                        "strategy": "Emphasize lifestyle and convenience",
                        "budget_allocation": 35000,
                        "duration_weeks": 4
                    },
                    {
                        "target_audience": "Families with children",
                        "strategy": "Focus on spacious units and amenities",
                        "budget_allocation": 25000,
                        "duration_weeks": 4
                    },
                    {
                        "target_audience": "Remote workers",
                        "strategy": "Highlight co-working and connectivity",
                        "budget_allocation": 20000,
                        "duration_weeks": 4
                    }
                ],
                "seasonal_factors": {
                    "current_season": "early_summer",
                    "peak_leasing_season": True,
                    "tourist_season": True,
                    "school_break": True
                },
                "market_conditions": {
                    "economic_index": 78,
                    "employment_growth": 3.2,
                    "migration_trend": "positive",
                    "construction_activity": "moderate"
                }
            },
            "photo_inventory": [
                {"type": "living_room", "count": 3},
                {"type": "kitchen", "count": 2},
                {"type": "bedroom", "count": 3},
                {"type": "bathroom", "count": 2},
                {"type": "amenity", "count": 5},
                {"type": "exterior", "count": 4}
            ],
            "marketing_history": {
                "last_campaign": {
                    "date": "2026-04-01",
                    "levers_used": ["convenience", "lifestyle"],
                    "platforms": ["instagram", "facebook", "google"],
                    "impressions": 125000,
                    "leads": 340,
                    "conversions": 28
                },
                "average_ctr": 2.8,
                "average_conversion_rate": 8.2
            }
        },
        {
            "id": "downtown_modern",
            "name": "Downtown Modern Lofts",
            "address": "456 Central Avenue, Austin, TX",
            "market_data": {
                "vacancy_by_floorplan": {
                    "1bed_loft": "1.5%",
                    "2bed_loft": "3%",
                    "penthouse": "8%"
                },
                "current_pricing": {
                    "1bed_loft": 2200,
                    "2bed_loft": 3200,
                    "penthouse": 5000
                },
                "active_concessions": [
                    {
                        "name": "Premium Waived",
                        "description": "$500 off first 2 months",
                        "floorplans": ["penthouse"],
                        "value": 1000,
                        "end_date": "2026-08-31"
                    }
                ],
                "occupancy_rate": 97.1,
                "priority_floorplans": ["1bed_loft"],
                "local_amenities": [
                    "5th street nightlife district",
                    "Michelin-starred restaurants",
                    "Arts and culture district",
                    "Music venues and theaters",
                    "Tech hub and startups",
                    "Bike-friendly streets"
                ],
                "property_amenities": [
                    "Rooftop bar and lounge",
                    "Artist-in-residence program",
                    "Soundproof music studios",
                    "Event space and gallery",
                    "Smart home integration",
                    "24-hour doorman"
                ],
                "concession_triggered": False,
                "triggered_floorplans": [],
                "trigger_reason": "N/A",
                "competitor_report": {
                    "primary_competitors": [
                        {
                            "name": "Arts Lofts Downtown",
                            "distance": "0.1 mi",
                            "avg_price_1bed": 2150,
                            "occupancy": 98,
                            "key_amenities": ["Gallery", "Artist spaces", "Events"]
                        },
                        {
                            "name": "Central Urban Residences",
                            "distance": "0.4 mi",
                            "avg_price_1bed": 2100,
                            "occupancy": 95,
                            "key_amenities": ["Rooftop", "Gym", "Valet"]
                        }
                    ],
                    "market_trend": "Strong demand for urban living",
                    "competitor_concessions": "Minimal - market is hot"
                },
                "optimization_briefs": [
                    {
                        "target_audience": "Creative professionals and artists",
                        "strategy": "Emphasize artistic community and cultural lifestyle",
                        "budget_allocation": 30000,
                        "duration_weeks": 4
                    },
                    {
                        "target_audience": "Urban professionals",
                        "strategy": "Highlight nightlife and walkability",
                        "budget_allocation": 25000,
                        "duration_weeks": 4
                    }
                ],
                "seasonal_factors": {
                    "current_season": "early_summer",
                    "peak_leasing_season": True,
                    "tourist_season": True,
                    "event_season": "festivals and concerts"
                },
                "market_conditions": {
                    "economic_index": 85,
                    "employment_growth": 4.1,
                    "migration_trend": "very_positive",
                    "construction_activity": "active"
                }
            },
            "photo_inventory": [
                {"type": "loft_living", "count": 3},
                {"type": "industrial_design", "count": 2},
                {"type": "rooftop", "count": 3},
                {"type": "gallery_space", "count": 2},
                {"type": "nightlife_view", "count": 2},
                {"type": "street_view", "count": 3}
            ],
            "marketing_history": {
                "last_campaign": {
                    "date": "2026-04-15",
                    "levers_used": ["lifestyle", "community"],
                    "platforms": ["instagram", "tiktok", "facebook"],
                    "impressions": 180000,
                    "leads": 420,
                    "conversions": 45
                },
                "average_ctr": 3.2,
                "average_conversion_rate": 10.7
            }
        },
        {
            "id": "suburban_family",
            "name": "Suburban Family Communities",
            "address": "789 Oak Ridge Drive, Austin, TX",
            "market_data": {
                "vacancy_by_floorplan": {
                    "2bed_2bath": "5%",
                    "3bed_2bath": "6%",
                    "3bed_3bath": "8%"
                },
                "current_pricing": {
                    "2bed_2bath": 1500,
                    "3bed_2bath": 1900,
                    "3bed_3bath": 2200
                },
                "active_concessions": [
                    {
                        "name": "Family Move-In",
                        "description": "Free first month + waived fees",
                        "floorplans": ["2bed_2bath", "3bed_2bath"],
                        "value": 1500,
                        "end_date": "2026-07-31"
                    },
                    {
                        "name": "Summer Specials",
                        "description": "$200 off monthly rent",
                        "floorplans": ["all"],
                        "value": 200,
                        "end_date": "2026-08-31"
                    }
                ],
                "occupancy_rate": 91.2,
                "priority_floorplans": ["2bed_2bath", "3bed_2bath"],
                "local_amenities": [
                    "Top-rated school district (Westlake ISD)",
                    "Family parks and playgrounds",
                    "Shopping and dining options",
                    "Community centers and libraries",
                    "Sports facilities and pools",
                    "Easy highway access"
                ],
                "property_amenities": [
                    "Olympic-sized pool with kids area",
                    "Playground and splash pad",
                    "Sports courts (tennis, basketball)",
                    "Community center and event spaces",
                    "Fitness center for families",
                    "Safe, gated community"
                ],
                "concession_triggered": True,
                "triggered_floorplans": ["2bed_2bath"],
                "trigger_reason": "Higher vacancy in 2bed units, back-to-school season approaching",
                "competitor_report": {
                    "primary_competitors": [
                        {
                            "name": "Westlake Family Living",
                            "distance": "1 mi",
                            "avg_price_3bed": 2100,
                            "occupancy": 94,
                            "key_amenities": ["Schools", "Pool", "Safe"]
                        },
                        {
                            "name": "Oak Hill Residences",
                            "distance": "0.7 mi",
                            "avg_price_3bed": 1950,
                            "occupancy": 93,
                            "key_amenities": ["Family-friendly", "Spacious", "Parking"]
                        }
                    ],
                    "market_trend": "Steady demand as families move to suburbs",
                    "competitor_concessions": "Competitive - many are offering specials"
                },
                "optimization_briefs": [
                    {
                        "target_audience": "Growing families",
                        "strategy": "Emphasize space, schools, and safety",
                        "budget_allocation": 40000,
                        "duration_weeks": 6
                    },
                    {
                        "target_audience": "Families relocating to Austin",
                        "strategy": "Highlight community and schools",
                        "budget_allocation": 35000,
                        "duration_weeks": 6
                    },
                    {
                        "target_audience": "First-time renters with children",
                        "strategy": "Focus on affordability and family features",
                        "budget_allocation": 25000,
                        "duration_weeks": 6
                    }
                ],
                "seasonal_factors": {
                    "current_season": "early_summer",
                    "peak_leasing_season": True,
                    "back_to_school_season": "approaching",
                    "family_vacation_period": True
                },
                "market_conditions": {
                    "economic_index": 72,
                    "employment_growth": 2.8,
                    "migration_trend": "positive_families",
                    "construction_activity": "moderate"
                }
            },
            "photo_inventory": [
                {"type": "kitchen", "count": 3},
                {"type": "family_living", "count": 3},
                {"type": "bedroom", "count": 3},
                {"type": "outdoor_amenities", "count": 4},
                {"type": "pool_area", "count": 3},
                {"type": "community", "count": 3}
            ],
            "marketing_history": {
                "last_campaign": {
                    "date": "2026-03-01",
                    "levers_used": ["family", "affordability", "safety"],
                    "platforms": ["facebook", "nextdoor", "google"],
                    "impressions": 95000,
                    "leads": 220,
                    "conversions": 18
                },
                "average_ctr": 2.3,
                "average_conversion_rate": 8.2
            }
        }
    ]
}


def get_campaign_strategist_input(property_id: str) -> dict:
    """
    Prepare input data for campaign_strategist agent from mock database
    
    Returns complete market data, competitor analysis, and optimization briefs
    """
    for prop in CAMPAIGN_STRATEGIST_MOCK_DATA["properties"]:
        if prop["id"] == property_id:
            return {
                "property_id": property_id,
                "property_name": prop["name"],
                "property_address": prop["address"],
                "vacancy_by_floorplan": prop["market_data"]["vacancy_by_floorplan"],
                "current_pricing": prop["market_data"]["current_pricing"],
                "active_concessions": prop["market_data"]["active_concessions"],
                "occupancy_rate": prop["market_data"]["occupancy_rate"],
                "priority_floorplans": prop["market_data"]["priority_floorplans"],
                "local_amenities": prop["market_data"]["local_amenities"],
                "property_amenities": prop["market_data"]["property_amenities"],
                "concession_triggered": prop["market_data"]["concession_triggered"],
                "triggered_floorplans": prop["market_data"]["triggered_floorplans"],
                "competitor_report": prop["market_data"]["competitor_report"],
                "optimization_briefs": prop["market_data"]["optimization_briefs"],
                "seasonal_factors": prop["market_data"]["seasonal_factors"],
                "market_conditions": prop["market_data"]["market_conditions"],
                "marketing_history": prop["marketing_history"]
            }
    return {}


def get_all_properties() -> list:
    """Get list of all properties"""
    return [(prop["id"], prop["name"]) for prop in CAMPAIGN_STRATEGIST_MOCK_DATA["properties"]]


if __name__ == "__main__":
    print("📊 CAMPAIGN STRATEGIST MOCK DATABASE")
    print("=" * 60)
    
    for prop_id, prop_name in get_all_properties():
        data = get_campaign_strategist_input(prop_id)
        print(f"\n✅ {prop_name}")
        print(f"   • Occupancy: {data['occupancy_rate']}%")
        print(f"   • Priority Floorplans: {', '.join(data['priority_floorplans'])}")
        print(f"   • Concession Triggered: {data['concession_triggered']}")
        print(f"   • Active Concessions: {len(data['active_concessions'])}")
        print(f"   • Competitors: {len(data['competitor_report']['primary_competitors'])}")
        print(f"   • Optimization Briefs: {len(data['optimization_briefs'])}")
