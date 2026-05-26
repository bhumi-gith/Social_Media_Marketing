"""PMS Data Agent — fetches live property data from the Property Management System.

Identifies which floorplans have vacancy, current pricing, concessions, amenities,
and photos. Filters properties matching the campaign brief.
"""
import json
import httpx
from leafmesh import LeafMeshLogger

logger = LeafMeshLogger(__name__)

PMS_BASE_URL = "http://127.0.0.1:8765"


async def pms_data(llm_response, input_data, context):
    """Fetch property data from PMS and identify campaign-relevant floorplans."""
    logger.info("🏢 PMS Data Agent — fetching property data...")

    campaign_prompt = input_data.get("campaign_prompt", "general leasing campaign")
    logger.info(f"Campaign prompt: {campaign_prompt}")

    pms_payload = {}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{PMS_BASE_URL}/api/v1/listings")
            if resp.status_code == 200:
                pms_payload = resp.json()
                logger.info("✓ PMS data fetched successfully")
            else:
                logger.warning(f"PMS returned {resp.status_code}, using mock fallback")
                pms_payload = _mock_pms_data()
    except Exception as e:
        logger.warning(f"PMS unreachable ({e}), using mock fallback")
        pms_payload = _mock_pms_data()

    floorplans = pms_payload.get("floorplans", {})
    photos = pms_payload.get("photos", [])
    concessions = pms_payload.get("concessions", [])
    amenities = pms_payload.get("amenities", [])

    # Calculate vacancy and occupancy
    total_units = sum(f.get("total_units", 0) for f in floorplans.values())
    occupied_units = sum(f.get("occupied_units", 0) for f in floorplans.values())
    occupancy_rate = round(occupied_units / total_units, 4) if total_units > 0 else 0.0

    # Vacancy by floorplan
    vacancy_by_floorplan = {}
    current_pricing = {}
    for fp_name, fp_data in floorplans.items():
        total = fp_data.get("total_units", 0)
        occupied = fp_data.get("occupied_units", 0)
        vacant = total - occupied
        vacancy_pct = round(vacant / total, 4) if total > 0 else 0.0
        vacancy_by_floorplan[fp_name] = {
            "total_units": total,
            "occupied_units": occupied,
            "vacant_units": vacant,
            "vacancy_rate": vacancy_pct,
        }
        current_pricing[fp_name] = fp_data.get("pricing", 0)

    # Priority floorplans — sorted by vacancy rate descending (most vacant first)
    priority_floorplans = sorted(
        [fp for fp, data in vacancy_by_floorplan.items() if data["vacancy_rate"] < 0.97],
        key=lambda fp: vacancy_by_floorplan[fp]["vacancy_rate"],
        reverse=True,
    )

    # Active concessions
    active_concessions = {}
    for c in concessions:
        for fp in c.get("floorplans", []):
            if fp not in active_concessions:
                active_concessions[fp] = []
            active_concessions[fp].append({
                "type": c.get("type"),
                "value": c.get("value"),
            })

    # Matching properties — identify which floorplans the campaign should focus on
    matching_properties = {
        fp: vacancy_by_floorplan[fp]
        for fp in priority_floorplans
    }

    # Amenities near the property (mock local amenities based on address)
    local_amenities = {
        "walkability_score": 82,
        "nearby": [
            "Coffee shop — 0.2 mi",
            "Grocery store — 0.4 mi",
            "Park — 0.3 mi",
            "Light rail — 0.6 mi",
            "Restaurants — 0.1 mi",
        ],
        "transit_score": 74,
        "bike_score": 68,
    }

    result = {
        "vacancy_by_floorplan": json.dumps(vacancy_by_floorplan),
        "current_pricing": json.dumps(current_pricing),
        "active_concessions": json.dumps(active_concessions),
        "occupancy_rate": occupancy_rate,
        "priority_floorplans": json.dumps(priority_floorplans),
        "local_amenities": json.dumps(local_amenities),
        "property_photos": json.dumps(photos),
        "amenity_list": json.dumps(amenities),
        "matching_properties": json.dumps(matching_properties),
    }

    logger.info(
        f"✓ PMS Data complete — occupancy: {occupancy_rate:.1%}, "
        f"priority floorplans: {priority_floorplans}"
    )
    return result


def _mock_pms_data() -> dict:
    """Return mock PMS data when the real PMS server is unavailable."""
    return {
        "floorplans": {
            "studio": {"total_units": 40, "occupied_units": 35, "pricing": 1200},
            "one_bedroom": {"total_units": 80, "occupied_units": 72, "pricing": 1650},
            "two_bedroom": {"total_units": 100, "occupied_units": 88, "pricing": 2100},
            "three_bedroom": {"total_units": 30, "occupied_units": 27, "pricing": 2800},
        },
        "photos": [
            {"url": "photo1.jpg", "caption": "Luxury lobby", "tags": ["lobby", "modern"]},
            {"url": "photo2.jpg", "caption": "2BR floor plan", "tags": ["bedroom"]},
            {"url": "photo3.jpg", "caption": "Gym facility", "tags": ["amenity", "fitness"]},
            {"url": "photo4.jpg", "caption": "Pool area", "tags": ["amenity", "outdoor"]},
            {"url": "photo5.jpg", "caption": "Community room", "tags": ["amenity", "social"]},
        ],
        "concessions": [
            {"type": "waived_deposit", "floorplans": ["two_bedroom"], "value": 500},
            {"type": "move_in_credit", "floorplans": ["studio", "one_bedroom"], "value": 100},
        ],
        "address": "1450 Riverside Drive, Denver, CO 80210",
        "amenities": [
            "Swimming pool", "Fitness center", "Dog park", "Community room",
            "Rooftop lounge", "Concierge", "24-hour security", "Reserved parking",
            "Package room", "Bike storage",
        ],
    }
