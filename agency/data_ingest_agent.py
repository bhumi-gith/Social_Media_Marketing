import httpx
from leafmesh import LeafMeshLogger

logger = LeafMeshLogger(__name__)

async def data_ingest(llm_response, input_data, context):
    logger.info("Running data_ingest agent...")
    property_ids = input_data.get("property_ids", "")
    
    # Pull from PMS (RealPage/Yardi/Entrata)
    # For testing, use mock PMS on localhost; for production, use actual PMS
    import os
    if os.getenv("USE_MOCK_PMS"):
        PMS_API_URL = "http://127.0.0.1:8765/api/v1"
        PMS_API_KEY = "test-key"
    else:
        PMS_API_URL = "https://your-pms-api.com/api/v1"
        PMS_API_KEY = "your-api-key"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PMS_API_URL}/listings",
                headers={"Authorization": f"Bearer {PMS_API_KEY}"},
                params={"property_ids": property_ids},
                timeout=30.0
            )
            pms_data = response.json()
    except Exception as e:
        logger.error(f"PMS connection failed: {e}")
        # PMS connection failed — halt pipeline or return fallback
        return {
            "vacancy_by_floorplan": "{}",
            "current_pricing": "{}",
            "active_concessions": "[]",
            "occupancy_rate": 0,
            "priority_floorplans": "[]",
            "local_amenities": "not available",
            "property_photos": "[]",
            "amenity_list": "[]",
        }
    
    # Parse and validate the data
    floorplans = pms_data.get("floorplans", {})
    photos = pms_data.get("photos", [])
    concessions = pms_data.get("concessions", [])
    
    # Calculate vacancy by floorplan
    vacancy_by_floorplan = {}
    
    for fp_name, fp_data in floorplans.items():
        total = fp_data.get("total_units", 0)
        occupied = fp_data.get("occupied_units", 0)
        vacancy_rate = ((total - occupied) / total * 100) if total > 0 else 0
        vacancy_by_floorplan[fp_name] = round(100 - vacancy_rate, 1)
    
    # Overall occupancy rate
    total_units = sum(fp.get("total_units", 0) for fp in floorplans.values())
    occupied_units = sum(fp.get("occupied_units", 0) for fp in floorplans.values())
    occupancy_rate = round((occupied_units / total_units * 100), 1) if total_units > 0 else 0
    
    # Priority floorplans — sorted by lowest occupancy first
    priority_floorplans = sorted(
        vacancy_by_floorplan.items(),
        key=lambda x: x[1]
    )
    
    # Pull local amenities from Google Places
    local_amenities = "not available"
    property_address = pms_data.get("address", "")
    
    if property_address:
        try:
            GOOGLE_API_KEY = "your-google-places-api-key"
            async with httpx.AsyncClient() as client:
                places_response = await client.get(
                    "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
                    params={
                        "location": pms_data.get("coordinates", ""),
                        "radius": 1600,
                        "type": "restaurant|grocery_or_supermarket|park",
                        "key": GOOGLE_API_KEY
                    },
                    timeout=15.0
                )
                places_data = places_response.json()
                nearby_places = [
                    p.get("name") for p in places_data.get("results", [])[:10]
                ]
                local_amenities = ", ".join(nearby_places)
        except Exception as e:
            logger.warning(f"Google Places API failed: {e}")
            local_amenities = "not available"
    
    return {
        "vacancy_by_floorplan": str(vacancy_by_floorplan),
        "current_pricing": str({k: v.get("pricing") for k, v in floorplans.items()}),
        "active_concessions": str(concessions),
        "occupancy_rate": occupancy_rate,
        "priority_floorplans": str([fp[0] for fp in priority_floorplans]),
        "local_amenities": local_amenities,
        "property_photos": str(photos),
        "amenity_list": str(pms_data.get("amenities", [])),
    }
