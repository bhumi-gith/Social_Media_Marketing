# LeafMesh Agent Testing Guide

## Overview
This guide provides comprehensive test datasets for the LeafMesh multifamily apartment marketing mesh. All test data is located in `/tests/`.

## Test Datasets Available

### 1. **test_property_data.json** — Data Ingest Agent Input
Property information, vacancy rates, pricing, amenities, and local area data.

**Key Fields:**
- `vacancy_data` — occupancy rates by floorplan
- `pricing` — current and concession-adjusted rates
- `amenities` — community and unit features
- `photos` — property image references
- `local_amenities` — walkable restaurants, parks, transit, schools

**How to Use:**
Test the `data_ingest` agent entry point with this data to trigger the full campaign pipeline.

---

### 2. **test_competitor_data.json** — Competitor Intel Agent Input
Competitive landscape monitoring data.

**Key Fields:**
- `competitors` — 3 competitor properties with pricing, concessions, reviews, ad activity
- `market_intelligence` — market positioning and trends

**How to Use:**
Run the `competitor_intel` agent independently to fetch competitive analysis, or feed results into `campaign_strategist`.

---

### 3. **test_campaign_briefs.json** — Campaign Strategist Output
Strategic campaign direction for visual and copywriting teams.

**Key Fields:**
- `campaign_briefs` — 3 briefs (family, young professional, budget-conscious)
- `summary` — budget allocation, levers, platforms

**How to Use:**
Pass these briefs to `visual_creator` and `copywriter` agents (run in parallel).

---

### 4. **test_visual_packages.json** — Visual Creator Agent Output
Creative visual direction, video scripts, carousel designs.

**Key Fields:**
- `visual_packages` — photo selections, carousel structures, video scripts, visual tone
- `platform_formats` — Instagram, TikTok, Meta format specifications

**How to Use:**
This output goes to `human_approval` agent along with copy packages for final review.

---

### 5. **test_copy_packages.json** — Copywriter Agent Output
Ad copy variants, Craigslist listings, platform-specific messaging.

**Key Fields:**
- `copy_packages` — 10 ad copy variants with hooks, headlines, CTAs
- `craigslist_listings` — 2 detailed Craigslist listings
- `fair_housing_violations` — compliance check (should be 0)

**How to Use:**
This output goes to `human_approval` agent along with visual packages.

---

### 6. **test_performance_metrics.json** — Performance Engine Input
Live campaign metrics from Meta, Instagram, TikTok, and CRM.

**Key Fields:**
- `campaigns` — 4 active campaigns with spend, leads, tours, leases
- `aggregate_metrics` — summary performance data
- `performance_by_lever` — which emotional levers work best
- `performance_by_platform` — platform efficiency rankings

**How to Use:**
Feed this to `performance_engine` agent to generate optimization briefs sent back to `campaign_strategist`.

---

## Testing Workflows

### Workflow 1: Full Pipeline (Entry Point)
**Trigger:** Data Ingest → Campaign Strategist → Visual Creator + Copywriter (parallel) → Human Approval → Publisher → Performance Engine

```bash
curl -X POST http://127.0.0.1:18820/api/mesh/request \
  -H "Content-Type: application/json" \
  -d @tests/test_property_data.json
```

### Workflow 2: Test Visual Creator Directly
**Input Data:**
```json
{
  "campaign_briefs": "<paste from test_campaign_briefs.json>",
  "property_photos": "<paste from test_property_data.json photos section>",
  "local_amenities": "<paste from test_property_data.json amenities section>",
  "amenity_list": "<paste from test_property_data.json amenities.community>"
}
```

### Workflow 3: Test Copywriter Directly
**Input Data:**
```json
{
  "campaign_briefs": "<paste from test_campaign_briefs.json>",
  "current_pricing": "<paste from test_property_data.json pricing>",
  "active_concessions": "<paste from test_property_data.json active_concessions>",
  "local_amenities": "<paste from test_property_data.json local_amenities>",
  "amenity_list": "<paste from test_property_data.json amenities.community>"
}
```

### Workflow 4: Test Human Approval
**Input Data:** Combine outputs from visual_creator + copywriter:
```json
{
  "visual_packages": "<from test_visual_packages.json>",
  "copy_packages": "<from test_copy_packages.json>",
  "campaign_briefs": "<from test_campaign_briefs.json>"
}
```

### Workflow 5: Test Performance Engine
**Input Data:**
```json
{
  "published_campaigns": "<campaign IDs>",
  "variant_ids_live": "<comma-separated variant IDs>",
  "daily_spend": 1120,
  "leads_tagged": 125,
  "meta_campaign_ids": "<paste from metrics>"
}
```

---

## Data Fields Reference

### Campaign Brief Structure
```json
{
  "brief_id": "brief_001",
  "target_floorplan": "2-Bedroom",
  "renter_persona": "family|young_professional|budget_conscious|pet_owner|student|relocator",
  "emotional_lever": "affordability|convenience|flexibility|urgency|pet_friendliness|move_in_ease|local_lifestyle",
  "messaging_direction": "2-3 sentences for creative teams",
  "local_lifestyle_hooks": ["specific nearby places"],
  "budget_allocation": 600,
  "platform_priority": ["meta_ads", "instagram_organic", "tiktok", "zumper", "craigslist"],
  "concession_flag": true|false
}
```

### Performance Metrics Structure
```json
{
  "campaign_id": "meta_2bed_family_001",
  "variant_id": "var_family_001",
  "platform": "meta|instagram|tiktok|craigslist|zumper",
  "spend": 450,
  "leads": 47,
  "cost_per_lead": 9.57,
  "tours_booked": 12,
  "cost_per_tour": 37.5,
  "leases_signed": 2,
  "cost_per_lease": 225
}
```

---

## Expected Agent Outputs

### data_ingest
```json
{
  "vacancy_by_floorplan": "string",
  "current_pricing": "string",
  "active_concessions": "string",
  "occupancy_rate": 0.885,
  "priority_floorplans": "string",
  "local_amenities": "string",
  "property_photos": "string",
  "amenity_list": "string"
}
```

### campaign_strategist
```json
{
  "campaign_briefs": "string (3 briefs)",
  "total_budget_allocated": 1500,
  "briefs_count": 3,
  "levers_used": "string",
  "platforms_targeted": "string",
  "concession_included": true
}
```

### visual_creator
```json
{
  "visual_packages": "string (complete design specs)",
  "briefs_covered": 3,
  "formats_produced": 8,
  "video_scripts_count": 2,
  "carousel_count": 3
}
```

### copywriter
```json
{
  "copy_packages": "string (10 variants)",
  "variants_count": 10,
  "fair_housing_violations": 0,
  "craigslist_listings": "string",
  "platforms_covered": "string",
  "hooks_produced": 13
}
```

### performance_engine
```json
{
  "daily_report": "string",
  "top_performers": "string",
  "underperformers": "string",
  "optimization_briefs": "string",
  "cost_per_lease": "string",
  "occupancy_impact": "string"
}
```

---

## Testing Tips

1. **Start Simple:** Test individual agents first (visual_creator, copywriter) before full workflows
2. **Check Outputs:** Verify agent outputs match expected schema before feeding to downstream agents
3. **Monitor Logs:** Watch for temperature warnings (competitor_intel, performance_engine use temp=0.7)
4. **API Keys:** Ensure OpenAI API key has access to gpt-4o and gpt-4o-mini models
5. **Fair Housing:** Copywriter should always return `fair_housing_violations: 0`
6. **Budget:** Verify `total_budget_allocated` doesn't exceed daily ceiling
7. **Performance Data:** CPT (cost per tour) matters more than CPL (cost per lead)

---

## Troubleshooting

### OpenAI API Errors
- Verify OPENAI_API_KEY in `.env`
- Check account has active billing and gpt-4o access
- Ensure API key hasn't been revoked

### JSON Parsing Errors
- Use JSON validator (jsonlint.com) to check test data
- Ensure all required fields are present
- Watch for type mismatches (number vs string)

### Agent Routing Issues
- Check `can_call` conditions in config.yaml
- Verify agent names match exactly (case-sensitive)
- Ensure input yields are available for next agent

---

## Quick Start Example

```bash
# 1. Start server
python3 main.py

# 2. In another terminal, trigger data_ingest entry point
curl -X POST http://127.0.0.1:18820/api/mesh/request \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test" \
  -d '{
    "entry_point": "marketing_pipeline",
    "input": {
      "property_data": "use_test_property_data",
      "competitor_data": "use_test_competitor_data"
    }
  }'

# 3. Watch logs for agent execution and results
```

---

## File Locations
- **Property Data:** `tests/test_property_data.json`
- **Competitor Data:** `tests/test_competitor_data.json`
- **Campaign Briefs:** `tests/test_campaign_briefs.json`
- **Visual Packages:** `tests/test_visual_packages.json`
- **Copy Packages:** `tests/test_copy_packages.json`
- **Performance Metrics:** `tests/test_performance_metrics.json`
- **This Guide:** `tests/TEST_GUIDE.md` (you are here)
