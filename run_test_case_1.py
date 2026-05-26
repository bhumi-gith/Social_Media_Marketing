"""
Test Case 1: Happy Path - Direct Python SDK Execution

This script bypasses the HTTP API and calls the mesh directly using the Python SDK.
Useful for debugging API key issues while still validating the workflow.
"""
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
from leafmesh import LeafMesh, LeafMeshLogger

# Add agency to path for auto-discovery
sys.path.insert(0, str(Path(__file__).parent / "agency"))

load_dotenv()
logger = LeafMeshLogger(__name__)


async def main():
    """Run Test Case 1: Happy Path"""
    
    # Initialize mesh from config
    leafmesh = LeafMesh.from_yaml("configs/config.yaml")
    logger.info("✅ LeafMesh initialized from config.yaml")
    
    # Start the mesh (boots agents, Redis, etc.)
    await leafmesh.start()
    logger.info("✅ LeafMesh started")
    
    try:
        # Test Case 1 data - Happy Path (occupancy 80.5%, no triggers)
        test_data = {
            "message": "Test Case 1 - Happy Path Execution",
            "type": "test",
            "property_ids": "prop-mills-ave-dc",
            "daily_budget": 500,
            "occupancy_data": {
                "studios": {"occupied": 6, "total": 8},
                "one_br": {"occupied": 10, "total": 12},
                "two_br": {"occupied": 14, "total": 16},
                "three_br": {"occupied": 10, "total": 12},
            },
            "active_concessions": [],
        }
        
        logger.info("🚀 Triggering marketing_pipeline entry point...")
        logger.info(f"   Input: {test_data}")
        
        # Call the mesh directly via entry point
        result = await leafmesh.mesh_call(
            entry_point_name="marketing_pipeline",
            data=test_data,
            session_id="test-case-1-happy-path"
        )
        
        logger.info("✅ Test Case 1 completed successfully!")
        logger.info(f"📋 Result summary:")
        
        # Extract and display key results
        if isinstance(result, dict):
            for key, value in result.items():
                if not key.startswith('_'):  # Skip internal fields
                    logger.info(f"   {key}: {value}")
        else:
            logger.info(f"   {result}")
            
        return result
        
    except Exception as e:
        logger.error(f"❌ Test Case 1 failed: {e}", exc_info=True)
        raise
        
    finally:
        # Cleanup
        logger.info("🛑 Shutting down mesh...")
        await leafmesh.stop()
        logger.info("✅ Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
