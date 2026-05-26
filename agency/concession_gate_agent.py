import json
from leafmesh import LeafMeshLogger

logger = LeafMeshLogger(__name__)

async def concession_gate(llm_response, input_data, context):
    """Occupancy threshold monitor. Triggers concession campaigns when floorplan occupancy drops below 80%."""
    logger.info("Running concession_gate agent...")
    
    # Read inputs (safely convert to float if possible)
    try:
        occupancy_rate = float(input_data.get("occupancy_rate", 100))
    except (ValueError, TypeError):
        occupancy_rate = 100.0
        
    vacancy_raw = input_data.get("vacancy_by_floorplan", "")
    
    # Parse the vacancy_by_floorplan JSON string (or dictionary)
    vacancy_data = {}
    if isinstance(vacancy_raw, dict):
        vacancy_data = vacancy_raw
    elif isinstance(vacancy_raw, str) and vacancy_raw.strip().startswith("{"):
        try:
            vacancy_data = json.loads(vacancy_raw)
        except json.JSONDecodeError:
            logger.warning("Failed to parse vacancy_by_floorplan as JSON.")
    
    # Threshold check
    THRESHOLD = 80.0
    triggered_floorplans = []
    occupancies = []
    
    # Check each floorplan
    for floorplan, data in vacancy_data.items():
        # Handle both flat formats like {"1-Bed": 75} and nested like {"1-Bed": {"occupancy": 75}}
        if isinstance(data, dict):
            occ = float(data.get("occupancy", 100))
        else:
            try:
                occ = float(data)
            except (ValueError, TypeError):
                occ = 100.0
                
        occupancies.append(occ)
        if occ < THRESHOLD:
            triggered_floorplans.append(floorplan)
    
    # Determine if triggered
    concession_triggered = len(triggered_floorplans) > 0
    
    # Determine severity
    concession_type = ""
    concession_severity = ""
    
    if concession_triggered:
        # Find the lowest occupancy to determine severity
        lowest_occupancy = min(occupancies) if occupancies else occupancy_rate
        
        if lowest_occupancy >= 70:
            concession_severity = "mild"
            concession_type = "Waived application fee or reduced security deposit by 50%"
        elif lowest_occupancy >= 60:
            concession_severity = "moderate"
            concession_type = "First month free or $500 move-in bonus"
        else:
            concession_severity = "aggressive"
            concession_type = "2 months free or significant rent reduction"
    
    # Deactivation check
    deactivation_recommended = (not concession_triggered) and (occupancy_rate >= THRESHOLD)
    
    return {
        "concession_triggered": concession_triggered,
        "triggered_floorplans": str(triggered_floorplans),
        "concession_type": concession_type,
        "concession_severity": concession_severity,
        "occupancy_at_trigger": occupancy_rate,
        "deactivation_recommended": deactivation_recommended
    }
