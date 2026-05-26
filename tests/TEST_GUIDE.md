# LeafMesh Test Dataset Guide

## Overview

This guide explains the test dataset structure based on real property listing data (Century 21 format) and maps it to your LeafMesh agents' input/output schemas.

---

## Data Structure from Property Listings

### Real-World Property Data (Century 21 Reference)

```
Property: 2841 Mills Ave NE, Washington, DC
Price: $799,000
Year Built: 1910
Bedrooms: 4 | Bathrooms: 3 | Sq Ft: 1,988
Amenities: Fireplace, hardwood floors, renovated
Location: Across from Langdon Park, walkable to shops
```

### What Century 21 Provides:
1. **Property Metadata**: Address, price, year built, property type
2. **Unit Details**: Bedrooms, bathrooms, square footage
3. **Features**: Architectural style, materials, utilities
4. **Amenities**: Parks, shopping, transit, dining nearby
5. **Photos**: 15-20+ professional images (exteriors, units, amenities)
6. **Listing Status**: Active, price history, days on market

---

## Mapping to LeafMesh Data Ingest

The `data_ingest` agent transforms property database records into structured yields:

### Input (from Property Management System)
```
Property ID → Mills Avenue Apartments
PMS Records → Unit inventory by floorplan
Recent leases → Occupancy calculations
Photos → Local amenities search results
```

### Output Yields
| Field | Source | Format | Example |
|-------|--------|--------|---------|
| `vacancy_by_floorplan` | PMS inventory | Dict | `{"studio": 0.15, "1br": 0.22, ...}` |
| `current_pricing` | Pricing table | Dict | `{"studio": 1850, "1br": 2200, ...}` |
| `active_concessions` | Lease specials | String | `"First month 50% off"` |
| `occupancy_rate` | Units rented / Total | Number | `80.5` |
| `priority_floorplans` | Sorted by vacancy | JSON | `[{floorplan, occupancy, priority}]` |
| `local_amenities` | Google Places API | Dict | Parks, transit, dining, entertainment |
| `property_photos` | Photo library | JSON | `[{photo_id, type, description, url}]` |
| `amenity_list` | Property features | JSON | Fitness, recreation, smart living, services |

---

## Test Case Structure

### Each test case includes:

1. **Name & Scenario** - What's being tested
2. **Request Body** - Input to the mesh via `/execute` endpoint
3. **Expected Output** - What each agent should produce
4. **Assertions** - Validation rules

---

## Test Case 1: Happy Path

### Scenario
All systems operational. Healthy occupancy (80%+), no concessions needed, normal budget.

### Request Body
```json
{
  "entry_point": "marketing_pipeline",
  "session_id": "session-tc1-001",
  "property_ids": "prop-mills-ave-dc",
  "daily_budget": 500
}
```

### Data Flow
```
data_ingest (outputs vacancy, pricing, amenities)
  ↓
campaign_strategist (reads data, produces 2-3 briefs)
  ↓
visual_creator + copywriter (parallel - create assets)
  ↓
human_approval (fan-in gate - waits for both)
  ↓
publisher (posts to Meta, Instagram, TikTok)
  ↓
performance_engine (analyzes metrics)
```

### Key Assertions
✅ `occupancy_rate >= 80` - Healthy  
✅ `concession_triggered == false` - No discount needed  
✅ `briefs_count == 3` - Campaign strategist produces 3 briefs  
✅ `variants_count >= 3` - Copywriter produces 3+ variants  
✅ `published_campaigns` - Publisher posts successfully  

---

## Test Case 2: Concession Trigger

### Scenario
Low occupancy on 3BR and 1BR units. Concession gate should trigger.

### Occupancy Data
```json
{
  "occupancy_rate": 68.5,
  "vacancy_by_floorplan": {
    "studio": 0.85,
    "1br": 0.60,      ← Below 80% threshold
    "2br": 0.72,
    "3br": 0.55       ← Below 80% threshold
  }
}
```

### Expected concession_gate Output
```json
{
  "concession_triggered": true,
  "triggered_floorplans": ["3br", "1br"],
  "concession_severity": "aggressive",
  "concession_type": "first_month_free"
}
```

### Campaign Strategist Adaptation
When `concession_triggered == true`, strategist receives this in inputs and includes concession messaging:
- **Brief 1**: "3BR - Move-in incentive: First month free"
- **Brief 2**: "1BR - Limited time: Waived deposits"
- **Brief 3**: "2BR - Premium positioning (no concession)"

### Key Assertions
✅ `concession_triggered == true`  
✅ `3br` and `1br` in `triggered_floorplans`  
✅ `campaign_strategist.concession_included == true`  
✅ Strategy adjusts messaging to include concessions  

---

## Test Case 3: Fair Housing Compliance

### What to Test
Copywriter should **block** violations before human approval.

### Example Violations
```
❌ "Perfect for families with young children"
   Reason: Cannot advertise based on familial status

❌ "Great for professionals"
   Reason: Cannot target by occupation/socioeconomic status

❌ "Perfect ethnic neighborhood"
   Reason: Cannot mention race/national origin

✅ "Vibrant, walkable community"
   Reason: Generic, factual, compliant
```

### Expected Output
```json
{
  "fair_housing_violations": 3,
  "blocks_routing": true,
  "reason": "Cannot route to human_approval when violations present"
}
```

### Flow Interruption
```
copywriter (detects violations)
  ↓
Sets fair_housing_violations > 0
  ↓
cannot_call human_approval (condition: fair_housing_violations == 0 fails)
  ↓
Logs violations for review
  ↓
Requires regeneration
```

### Key Assertions
✅ `fair_housing_violations > 0`  
✅ Does NOT route to `human_approval`  
✅ Violations logged with specific phrases  
✅ Suggests compliant rewrites  

---

## Test Case 4: HITL Feedback Loop

### Scenario
Human approver wants to regenerate visuals with feedback.

### Human Response
```json
{
  "approval_status": "regenerate_visuals",
  "editor_notes": "Needs warmer colors for family audience. Video too fast-paced.",
  "reviewer_name": "Sarah Chen"
}
```

### Expected Routing
```
human_approval (approval_status == "regenerate_visuals")
  ↓
Triggers can_call rule: agent visual_creator
  ↓
visual_creator (receives editor feedback)
  ↓
Regenerates with warm_cozy visual tone
  ↓
Returns new visual_packages
  ↓
Back to human_approval for re-review
```

### Key Assertions
✅ `approval_status == "regenerate_visuals"` routes back to `visual_creator`  
✅ `editor_notes` passed through to next agent  
✅ Loop supports multiple iterations  
✅ No approval bypasses HITL gate  

---

## Test Case 5: Performance Analysis

### Scenario
Publisher has posted 3 campaigns. Performance engine analyzes results after 72 hours.

### Campaign Performance Data

| Campaign | Platform | Spend | Leads | CPL | Tours | CPT | Leases |
|----------|----------|-------|-------|-----|-------|------|--------|
| cam-001 | Instagram Reels | $150 | 48 | $3.13 | 18 | $8.33 | 2 |
| cam-002 | Meta Feed | $200 | 32 | $6.25 | 4 | $50 | 0 |
| cam-003 | TikTok | $150 | 92 | $1.63 | 28 | $5.36 | 4 |

### Expected Performance Engine Output
```json
{
  "top_performer": "cam-003 (TikTok)",
  "reason": "Lowest CPL ($1.63), CPT ($5.36), highest leases (4)",
  
  "underperformer": "cam-002 (Meta)",
  "reason": "Highest CPT ($50), zero leases, inefficient spend",
  
  "optimization_briefs": [
    "TikTok convenience messaging 3x more efficient than Meta affordability",
    "Increase TikTok budget 50%",
    "Pause Meta affordability messaging for 72 hours",
    "Instagram Reels maintaining solid performance (CPT $8.33)"
  ],
  
  "budget_recommendation": {
    "increase": ["cam-003"],
    "maintain": ["cam-001"],
    "pause": ["cam-002"]
  }
}
```

### Key Assertions
✅ CPT (cost per tour) prioritized over CPL  
✅ Underperformer flagged only after 72+ hours  
✅ Top performer gets budget increase  
✅ Optimization briefs guide next campaign cycle  

---

## How to Run Tests in Playground

### Step 1: Open Test Agent Workflow
In Leafcraft Playground → **Test Agent Workflow**

### Step 2: Configure Test
- **Entry Point**: Select `marketing_pipeline`
- **Request Body**: Copy test case JSON into the `data` field
- **Session ID**: Keep unique per test (system auto-generates)

### Step 3: Execute
Click **Execute** and monitor:
1. **Flow**: Watch agents execute in order
2. **Yields**: Check each agent's output
3. **Session Logs**: Review detailed execution logs
4. **Errors**: Catch validation/Fair Housing issues

### Step 4: Validate
Compare actual output to expected output in test case

---

## Running Priority Order

1. **Test 1 (Happy Path)** - Verify basic flow works
2. **Test 2 (Concession)** - Validate business logic
3. **Test 3 (Fair Housing)** - Safety/compliance
4. **Test 4 (HITL Loop)** - Human feedback integration
5. **Test 5 (Performance)** - Analytics & optimization
6. **Test 6 (Competitor)** - Strategy enrichment
7. **Test 7 (High Budget)** - Stress test

---

## Data Mapping Reference

### Property Database → LeafMesh

```
Century 21 Listing
├─ Photos (20+)
│  └─ data_ingest.property_photos
├─ Nearby Amenities
│  └─ data_ingest.local_amenities
├─ Property Features
│  └─ data_ingest.amenity_list
├─ Pricing History
│  └─ data_ingest.current_pricing
└─ Marketing Notes
   └─ campaign_strategist.inputs
```

### LeafMesh Flow

```
data_ingest (programmatic - pulls from PMS)
  ↓ outputs: vacancy, pricing, amenities, photos
campaign_strategist (LLM - makes strategic decisions)
  ↓ outputs: 2-3 briefs with budgets & platforms
visual_creator (LLM - creates visual assets)
  ↓ outputs: photo selections, video scripts, carousels
copywriter (LLM - creates copy variants)
  ↓ outputs: ad copy, Craigslist listings, CTAs
human_approval (HUMAN - fan-in gate with feedback loop)
  ↓ outputs: approval_status (approved/regenerate_*)
publisher (programmatic - posts to platforms)
  ↓ outputs: campaign IDs, variant tracking
performance_engine (LLM - analyzes results)
  ↓ outputs: optimization briefs → back to strategist
```

---

## Common Issues & Debugging

### Issue: Fair Housing Violations Block Flow
**Cause**: Copywriter detected familial/origin/status targeting  
**Solution**: Review violations, regenerate with generic language  
**Test**: Test Case 3

### Issue: Concession Gate Not Triggering
**Cause**: `occupancy_rate` >= 80% (not below threshold)  
**Solution**: Reduce `occupancy_rate` to < 0.80 in test data  
**Test**: Test Case 2

### Issue: HITL Approval Timeout
**Cause**: No human response within 300 seconds  
**Solution**: Approve/reject/regenerate within timeout window  
**Config**: `human_timeout_seconds: 300` in config.yaml

### Issue: Publisher Not Receiving Approved Copy
**Cause**: Copywriter `fair_housing_violations > 0` blocks routing  
**Solution**: Run Test Case 3 first to identify violations  
**Debug**: Check `copywriter.fair_housing_violations` yield

---

## Expected Test Dataset Size

- **8 Test Cases** covering all major flows
- **15 Property Photos** with metadata
- **12 Local Amenities** with distance/categories
- **50+ Copy Variants** in Fair Housing testing
- **5 Floorplans** (studio, 1BR, 2BR, 3BR, + commercial)

---

## Next Steps

1. ✅ Created `/tests/test_datasets.json` with 8 test cases
2. ⏭️ Load dataset into playground
3. ⏭️ Run Test Case 1 (Happy Path) first
4. ⏭️ Validate outputs match expected schemas
5. ⏭️ Iterate through remaining test cases
6. ⏭️ Document any deviations from expected behavior

