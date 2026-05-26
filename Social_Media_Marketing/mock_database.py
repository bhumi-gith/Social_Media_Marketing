"""
Mock Database for Visual Creator Agent
Contains: Campaign Briefs, Property Photos, Local Amenities, Amenity Listings
"""

MOCK_DATABASE = {
    "properties": [
        {
            "id": "riverside_luxury",
            "name": "Riverside Luxury Apartments",
            "address": "123 Waterfront Drive, Austin, TX",
            "campaign_briefs": [
                {
                    "id": "brief_family_001",
                    "persona": "family",
                    "floorplan": "2-Bedroom, 2-Bath",
                    "key_selling_points": [
                        "Pet-friendly with dog park",
                        "Top-rated schools nearby",
                        "Family-sized kitchens",
                        "Playground and splash pad"
                    ],
                    "emotional_lever": "move_in_ease",
                    "headline": "Family Love Living Here",
                    "subheadline": "Emphasize quick approval and family amenities"
                },
                {
                    "id": "brief_young_prof_001",
                    "persona": "young_professional",
                    "floorplan": "1-Bedroom, 1-Bath",
                    "key_selling_points": [
                        "Walking distance to downtown",
                        "Modern finishes and smart home",
                        "High-speed internet included",
                        "Rooftop lounge and co-working space"
                    ],
                    "emotional_lever": "convenience",
                    "headline": "Your 1-Bedroom Awaits You",
                    "subheadline": "Highlight walkability and modern lifestyle"
                },
                {
                    "id": "brief_budget_001",
                    "persona": "budget_conscious",
                    "floorplan": "Studio, 1-Bath",
                    "key_selling_points": [
                        "No move-in fees this month",
                        "Utilities included",
                        "Free fitness center",
                        "Parking included"
                    ],
                    "emotional_lever": "affordability",
                    "headline": "Luxury Doesn't Have to Break the Bank",
                    "subheadline": "Focus on value and accessible pricing"
                }
            ],
            "property_photos": [
                {
                    "id": "photo_001",
                    "title": "Modern Living Room with Natural Light",
                    "description": "Spacious living area with floor-to-ceiling windows overlooking the waterfront",
                    "room_type": "living_room",
                    "url": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=1280&q=80",
                    "alt_text": "Modern apartment living room with waterfront view"
                },
                {
                    "id": "photo_002",
                    "title": "Chef's Kitchen with Island",
                    "description": "Contemporary kitchen with stainless steel appliances and granite countertops",
                    "room_type": "kitchen",
                    "url": "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=1280&q=80",
                    "alt_text": "Modern kitchen with island and stainless steel appliances"
                },
                {
                    "id": "photo_003",
                    "title": "Master Bedroom Suite",
                    "description": "Luxurious bedroom with walk-in closet and ensuite bathroom",
                    "room_type": "bedroom",
                    "url": "https://images.unsplash.com/photo-1540932239986-310128078e6f?w=1280&q=80",
                    "alt_text": "Spacious master bedroom with modern furnishings"
                },
                {
                    "id": "photo_004",
                    "title": "Rooftop Lounge Area",
                    "description": "Panoramic city and waterfront views from our rooftop entertainment space",
                    "room_type": "amenity",
                    "url": "https://images.unsplash.com/photo-1582053921894-56ae519256ca?w=1280&q=80",
                    "alt_text": "Rooftop lounge with city skyline view"
                },
                {
                    "id": "photo_005",
                    "title": "Fitness Center",
                    "description": "State-of-the-art gym with cardio equipment, free weights, and yoga studio",
                    "room_type": "amenity",
                    "url": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=1280&q=80",
                    "alt_text": "Modern fitness center with gym equipment"
                }
            ],
            "amenity_listing": {
                "property_amenities": [
                    {
                        "name": "Fitness Center",
                        "description": "24/7 state-of-the-art gym with cardio, weights, and yoga classes",
                        "icon": "💪"
                    },
                    {
                        "name": "Rooftop Lounge",
                        "description": "Stunning 360° views with pool, hot tub, and entertainment area",
                        "icon": "🏊"
                    },
                    {
                        "name": "Dog Park",
                        "description": "Two-acre off-leash dog park with shade trees and water stations",
                        "icon": "🐕"
                    },
                    {
                        "name": "Co-Working Space",
                        "description": "High-speed fiber internet, meeting rooms, and quiet work areas",
                        "icon": "💼"
                    },
                    {
                        "name": "Gourmet Kitchen",
                        "description": "Chef-approved kitchens with premium appliances and smart home integration",
                        "icon": "👨‍🍳"
                    },
                    {
                        "name": "Smart Home Tech",
                        "description": "Keyless entry, smart thermostats, and app-controlled lighting",
                        "icon": "🏠"
                    },
                    {
                        "name": "Parking Garage",
                        "description": "Covered parking with EV charging stations available",
                        "icon": "🚗"
                    },
                    {
                        "name": "Pool & Spa",
                        "description": "Heated saltwater pool, hot tub, and luxury cabanas",
                        "icon": "🏊‍♀️"
                    }
                ],
                "local_amenities": [
                    {
                        "category": "Dining",
                        "name": "The Waterfront Restaurant District",
                        "distance": "0.3 miles",
                        "description": "20+ restaurants within walking distance, from casual to fine dining",
                        "icon": "🍽️"
                    },
                    {
                        "category": "Parks",
                        "name": "Riverside Park",
                        "distance": "0.2 miles",
                        "description": "50-acre waterfront park with trails, playgrounds, and picnic areas",
                        "icon": "🌳"
                    },
                    {
                        "category": "Shopping",
                        "name": "Downtown Shopping District",
                        "distance": "0.5 miles",
                        "description": "Boutiques, retail stores, and outdoor shopping venues",
                        "icon": "🛍️"
                    },
                    {
                        "category": "Transit",
                        "name": "Public Transportation Hub",
                        "distance": "0.1 miles",
                        "description": "Bus terminal and bike-share station for easy commuting",
                        "icon": "🚌"
                    },
                    {
                        "category": "Schools",
                        "name": "Top-Rated Schools",
                        "distance": "0.7 miles",
                        "description": "Award-winning elementary, middle, and high schools nearby",
                        "icon": "🏫"
                    },
                    {
                        "category": "Entertainment",
                        "name": "Entertainment Complex",
                        "distance": "0.6 miles",
                        "description": "Movie theater, bowling alley, and gaming center",
                        "icon": "🎬"
                    },
                    {
                        "category": "Health",
                        "name": "Medical Center",
                        "distance": "0.8 miles",
                        "description": "Full-service hospital and urgent care facility",
                        "icon": "🏥"
                    },
                    {
                        "category": "Coffee",
                        "name": "Specialty Coffee Shops",
                        "distance": "0.2 miles",
                        "description": "5+ artisan coffee and tea shops in the neighborhood",
                        "icon": "☕"
                    }
                ]
            }
        },
        {
            "id": "downtown_modern",
            "name": "Downtown Modern Lofts",
            "address": "456 Central Avenue, Austin, TX",
            "campaign_briefs": [
                {
                    "id": "brief_young_prof_002",
                    "persona": "young_professional",
                    "floorplan": "1-Bedroom Loft",
                    "key_selling_points": [
                        "Prime downtown location",
                        "Industrial chic design",
                        "Exposed brick and floor-to-ceiling windows",
                        "24-hour doorman service"
                    ],
                    "emotional_lever": "convenience",
                    "headline": "Live Where the Action Is",
                    "subheadline": "Urban lifestyle at your doorstep"
                },
                {
                    "id": "brief_creative_001",
                    "persona": "creative_professional",
                    "floorplan": "2-Bedroom Loft",
                    "key_selling_points": [
                        "Artist-friendly community",
                        "Open floor plans for creative living",
                        "Gallery wall installations",
                        "Regular artist events and exhibitions"
                    ],
                    "emotional_lever": "lifestyle",
                    "headline": "Create Your Masterpiece Here",
                    "subheadline": "Space designed for creative minds"
                }
            ],
            "property_photos": [
                {
                    "id": "photo_101",
                    "title": "Industrial Loft Interior",
                    "description": "Exposed brick, soaring ceilings, and natural skylights",
                    "room_type": "living_room",
                    "url": "https://images.unsplash.com/photo-1487231471519-e21cc028cb29?w=1280&q=80",
                    "alt_text": "Industrial style loft with exposed brick"
                },
                {
                    "id": "photo_102",
                    "title": "Modern Loft Kitchen",
                    "description": "Stainless steel open kitchen integrated into living space",
                    "room_type": "kitchen",
                    "url": "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=1280&q=80",
                    "alt_text": "Contemporary loft kitchen"
                },
                {
                    "id": "photo_103",
                    "title": "Floor-to-Ceiling Windows",
                    "description": "Panoramic city views and abundant natural light",
                    "room_type": "living_room",
                    "url": "https://images.unsplash.com/photo-1493857671505-72967e2e2760?w=1280&q=80",
                    "alt_text": "Modern apartment with floor-to-ceiling windows"
                },
                {
                    "id": "photo_104",
                    "title": "Building Lobby & Entrance",
                    "description": "Elegant glass and steel lobby with 24-hour concierge",
                    "room_type": "amenity",
                    "url": "https://images.unsplash.com/photo-1554995207-c18e38f605cb?w=1280&q=80",
                    "alt_text": "Modern building lobby entrance"
                }
            ],
            "amenity_listing": {
                "property_amenities": [
                    {
                        "name": "Concierge Service",
                        "description": "24/7 professional concierge for packages, reservations, and services",
                        "icon": "🎩"
                    },
                    {
                        "name": "Art Gallery Space",
                        "description": "Community gallery for resident art exhibitions and events",
                        "icon": "🎨"
                    },
                    {
                        "name": "Business Center",
                        "description": "Fully equipped with private offices and meeting rooms",
                        "icon": "💼"
                    },
                    {
                        "name": "Community Lounge",
                        "description": "High-design gathering space with premium furnishings",
                        "icon": "🪑"
                    }
                ],
                "local_amenities": [
                    {
                        "category": "Dining",
                        "name": "Michelin-Starred Restaurants",
                        "distance": "0.2 miles",
                        "description": "World-class dining establishments throughout downtown",
                        "icon": "🍽️"
                    },
                    {
                        "category": "Culture",
                        "name": "Museums & Galleries",
                        "distance": "0.3 miles",
                        "description": "Art museums, theaters, and cultural institutions",
                        "icon": "🎭"
                    },
                    {
                        "category": "Nightlife",
                        "name": "Live Music & Bars",
                        "distance": "0.1 miles",
                        "description": "Vibrant nightlife scene with live music venues and rooftop bars",
                        "icon": "🎵"
                    },
                    {
                        "category": "Transit",
                        "name": "Transit Hub",
                        "distance": "0.05 miles",
                        "description": "Central station with bus, light rail, and rideshare access",
                        "icon": "🚇"
                    },
                    {
                        "category": "Shopping",
                        "name": "Luxury Shopping",
                        "distance": "0.4 miles",
                        "description": "Designer boutiques and luxury retail shops",
                        "icon": "👜"
                    }
                ]
            }
        },
        {
            "id": "suburban_family",
            "name": "Suburban Family Communities",
            "address": "789 Oak Ridge Drive, Austin, TX",
            "campaign_briefs": [
                {
                    "id": "brief_family_002",
                    "persona": "family",
                    "floorplan": "3-Bedroom, 2-Bath",
                    "key_selling_points": [
                        "Quiet suburban setting",
                        "Top-rated school district",
                        "Spacious yards and playgrounds",
                        "Community pool and recreation center"
                    ],
                    "emotional_lever": "move_in_ease",
                    "headline": "Build Your Family Dream Here",
                    "subheadline": "Safe, spacious, and welcoming community"
                },
                {
                    "id": "brief_budget_002",
                    "persona": "budget_conscious",
                    "floorplan": "2-Bedroom, 2-Bath",
                    "key_selling_points": [
                        "Affordable family housing",
                        "All utilities included",
                        "Free community activities",
                        "No hidden fees guarantee"
                    ],
                    "emotional_lever": "affordability",
                    "headline": "Spacious Living, Smart Pricing",
                    "subheadline": "Quality family living you can afford"
                }
            ],
            "property_photos": [
                {
                    "id": "photo_201",
                    "title": "Suburban Home Exterior",
                    "description": "Beautiful residential community with manicured lawns and tree-lined streets",
                    "room_type": "exterior",
                    "url": "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=1280&q=80",
                    "alt_text": "Suburban community with homes and trees"
                },
                {
                    "id": "photo_202",
                    "title": "Family Kitchen & Dining",
                    "description": "Spacious kitchen with dining area perfect for family gatherings",
                    "room_type": "kitchen",
                    "url": "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=1280&q=80",
                    "alt_text": "Large family kitchen with dining space"
                },
                {
                    "id": "photo_203",
                    "title": "Kids' Playground",
                    "description": "Safe, modern playground equipment in community park",
                    "room_type": "amenity",
                    "url": "https://images.unsplash.com/photo-1552637881-98e72f77c869?w=1280&q=80",
                    "alt_text": "Community playground for children"
                },
                {
                    "id": "photo_204",
                    "title": "Community Pool",
                    "description": "Olympic-sized swimming pool with shallow end for young children",
                    "room_type": "amenity",
                    "url": "https://images.unsplash.com/photo-1576610616656-570ae76b641e?w=1280&q=80",
                    "alt_text": "Community swimming pool facility"
                },
                {
                    "id": "photo_205",
                    "title": "Sports Courts",
                    "description": "Basketball, tennis, and volleyball courts for active families",
                    "room_type": "amenity",
                    "url": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=1280&q=80",
                    "alt_text": "Community sports courts and facilities"
                }
            ],
            "amenity_listing": {
                "property_amenities": [
                    {
                        "name": "Swimming Pool",
                        "description": "Olympic-sized pool with shallow kids area and lap lanes",
                        "icon": "🏊‍♂️"
                    },
                    {
                        "name": "Playground",
                        "description": "Age-appropriate play equipment in safe, shaded area",
                        "icon": "🛝"
                    },
                    {
                        "name": "Sports Courts",
                        "description": "Basketball, tennis, and volleyball courts",
                        "icon": "🏀"
                    },
                    {
                        "name": "Community Center",
                        "description": "Meeting spaces, game room, and activity programs",
                        "icon": "🏛️"
                    },
                    {
                        "name": "Picnic Areas",
                        "description": "Covered pavilions with grills and seating",
                        "icon": "🌳"
                    }
                ],
                "local_amenities": [
                    {
                        "category": "Schools",
                        "name": "Top-Rated Schools",
                        "distance": "0.4 miles",
                        "description": "Award-winning elementary, middle, and high schools in district",
                        "icon": "🏫"
                    },
                    {
                        "category": "Parks",
                        "name": "Nature Preserve",
                        "distance": "0.5 miles",
                        "description": "Beautiful hiking and biking trails through natural landscape",
                        "icon": "🌲"
                    },
                    {
                        "category": "Shopping",
                        "name": "Family Shopping Mall",
                        "distance": "1 mile",
                        "description": "Retail stores, toy shops, and family restaurants",
                        "icon": "🛒"
                    },
                    {
                        "category": "Healthcare",
                        "name": "Pediatric Clinic",
                        "distance": "0.7 miles",
                        "description": "Family-friendly medical center with pediatric specialists",
                        "icon": "👨‍⚕️"
                    },
                    {
                        "category": "Entertainment",
                        "name": "Family Activities",
                        "distance": "1.2 miles",
                        "description": "Zoo, aquarium, and interactive museums for kids",
                        "icon": "🎠"
                    }
                ]
            }
        }
    ]
}


def get_campaign_brief(property_id: str, brief_id: str) -> dict:
    """Retrieve a specific campaign brief"""
    for prop in MOCK_DATABASE["properties"]:
        if prop["id"] == property_id:
            for brief in prop.get("campaign_briefs", []):
                if brief["id"] == brief_id:
                    return brief
    return None


def get_property_photos(property_id: str) -> list:
    """Retrieve all photos for a property"""
    for prop in MOCK_DATABASE["properties"]:
        if prop["id"] == property_id:
            return prop.get("property_photos", [])
    return []


def get_local_amenities(property_id: str) -> list:
    """Retrieve local amenities for a property"""
    for prop in MOCK_DATABASE["properties"]:
        if prop["id"] == property_id:
            return prop.get("amenity_listing", {}).get("local_amenities", [])
    return []


def get_amenity_listing(property_id: str) -> list:
    """Retrieve property amenities for a property"""
    for prop in MOCK_DATABASE["properties"]:
        if prop["id"] == property_id:
            return prop.get("amenity_listing", {}).get("property_amenities", [])
    return []


def get_all_properties() -> list:
    """Get list of all property IDs"""
    return [prop["id"] for prop in MOCK_DATABASE["properties"]]


def prepare_visual_creator_input(property_id: str, brief_ids: list = None) -> dict:
    """
    Prepare consolidated input data for visual_creator agent
    
    Returns dict with:
    - campaign_briefs: List of campaign briefs
    - property_photos: List of property photos
    - local_amenities: List of local amenities
    - amenity_listing: List of property amenities
    """
    
    property_data = None
    for prop in MOCK_DATABASE["properties"]:
        if prop["id"] == property_id:
            property_data = prop
            break
    
    if not property_data:
        return {}
    
    # Filter briefs if specific IDs provided
    campaign_briefs = property_data.get("campaign_briefs", [])
    if brief_ids:
        campaign_briefs = [b for b in campaign_briefs if b["id"] in brief_ids]
    
    return {
        "property_id": property_id,
        "property_name": property_data.get("name"),
        "property_address": property_data.get("address"),
        "campaign_briefs": campaign_briefs,
        "property_photos": property_data.get("property_photos", []),
        "local_amenities": property_data.get("amenity_listing", {}).get("local_amenities", []),
        "amenity_listing": property_data.get("amenity_listing", {}).get("property_amenities", [])
    }


if __name__ == "__main__":
    # Quick test
    print("📊 MOCK DATABASE STRUCTURE TEST")
    print("=" * 50)
    
    for prop_id in get_all_properties():
        input_data = prepare_visual_creator_input(prop_id)
        print(f"\n✅ Property: {input_data['property_name']}")
        print(f"   • Campaign Briefs: {len(input_data['campaign_briefs'])}")
        print(f"   • Property Photos: {len(input_data['property_photos'])}")
        print(f"   • Local Amenities: {len(input_data['local_amenities'])}")
        print(f"   • Property Amenities: {len(input_data['amenity_listing'])}")
