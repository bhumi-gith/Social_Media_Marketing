# Campaign Strategist Mock Database & Real Estate Marketing Framework

## Overview
This document outlines the mock database structure and real estate marketing strategy framework for the Campaign Strategist agent.

## Files Created

### 1. **campaign_strategist_mock_data.py** (Main Database File)
Location: `/SocialMediaMarketing_v2/campaign_strategist_mock_data.py`

This file contains comprehensive market data for 3 Austin-based properties:
- Riverside Luxury Apartments
- Downtown Modern Lofts  
- Suburban Family Communities

Each property includes:
- **Vacancy Data**: By floorplan with occupancy rates
- **Pricing**: Current rental rates per floorplan
- **Active Concessions**: Time-limited offers with values
- **Competitor Analysis**: 2 primary competitors per property with pricing/occupancy/amenities
- **Optimization Briefs**: 2-3 target audiences with recommended strategies and budgets
- **Market Conditions**: Economic index, employment growth, migration trends
- **Marketing History**: Past campaign performance (impressions, leads, conversions)

### 2. **Updated configs/config.yaml**
Lines 73-200 contain the NEW campaign_strategist agent system prompt with:
- Real estate-specific personas (young_professional, family_with_kids, remote_worker, etc.)
- Emotional levers tailored to apartment marketing (move_in_ease, convenience, affordability, community, family_safety)
- Specific headline examples for each persona + lever combination
- Platform selection guidance (Meta, Instagram, TikTok, Google Ads, Nextdoor, Craigslist)
- Strategic rules for budget allocation, concession messaging, and competitor differentiation
- JSON output format specification for campaign briefs

## Real Estate Marketing Intelligence

### Emotional Levers (Updated for Real Estate)
1. **move_in_ease**: Approval speed, transparent fees, weekend move-ins
2. **convenience**: Specific nearby amenities with walk times  
3. **affordability**: Value comparison vs competitors, bundled features
4. **community**: Events, programming, social spaces
5. **lifestyle**: Urban vibe, creative energy, specific market positioning
6. **family_safety**: Schools, gated communities, playgrounds, parks

### Target Personas

| Persona | Age | Priorities | Key Messaging | Platforms |
|---------|-----|-----------|---------------|-----------|
| Young Professional | 25-35 | Walkability, nightlife, flex space | Convenience, lifestyle | Meta, Instagram, TikTok |
| Family with Kids | 30-45 | Schools, safety, space | Family safety, affordability | Facebook, Nextdoor, Google |
| Remote Worker | Any | WiFi, quiet, flexibility | Convenience, community | Google Ads, Instagram |
| Relocating | Any | Ease, fast approval, virtual tours | Move-in ease | Google Ads, Meta |
| Budget Conscious | Any | Price, transparency, deals | Affordability | Craigslist, Meta, Google |
| Lifestyle/Creative | 25-40 | Unique design, events, community | Community, lifestyle | Instagram, TikTok |

### Market Segmentation Strategy
Properties are categorized by market position:
- **Premium Urban**: Downtown Modern Lofts (high occupancy, minimal concessions needed)
- **Luxury Suburban**: Riverside Luxury Apartments (high amenities, moderate vacancy)
- **Family-Friendly**: Suburban Family Communities (seasonal demand, aggressive concessions)

### Campaign Brief Structure (JSON Output)
Each brief includes:
```json
{
  "brief_id": 1,
  "target_floorplan": "1-bedroom",
  "renter_persona": "young_professional",
  "emotional_lever": "convenience",
  "headlines": ["Walk to Dinner. Drive to Your Dream Job.", "..."],
  "key_selling_points": ["3 min walk to tech offices", "15 min to downtown nightlife", "High-speed fiber internet"],
  "concession_message": "Limited-time: $200/month off first 2 months" OR null,
  "budget_allocation": 40000,
  "platform_priority": ["meta_ads", "instagram_organic", "google_ads"],
  "messaging_tone": "energetic, urban, modern"
}
```

## Integration with Visual Creator

Once Campaign Strategist generates briefs, the data flows to:

1. **Visual Creator**: Takes briefs + property photos + amenities → Generates HTML posters in 3 aspect ratios + PNG exports
2. **Copywriter**: Takes briefs → Generates ad copy, email subject lines, social captions
3. **Publisher**: Distributes assets across platforms specified in brief

## Using the Mock Database

### Load Campaign Strategist Input
```python
from campaign_strategist_mock_data import get_campaign_strategist_input

# Get input for Riverside Luxury Apartments
input_data = get_campaign_strategist_input("riverside_luxury")

# Returns dict with:
# - vacancy_by_floorplan
# - current_pricing  
# - active_concessions
# - competitor_report
# - optimization_briefs
# - market_conditions
# - marketing_history
```

### Properties Available
- `riverside_luxury`: Luxury waterfront, 94.2% occupancy, concessions triggered
- `downtown_modern`: Urban lofts, 97.1% occupancy, strong market
- `suburban_family`: Family communities, 91.2% occupancy, seasonal demand

## Key Marketing Insights from Mock Data

### Riverside Luxury Apartments
- **Challenge**: 1-bedroom vacancy at 3% (below target), concession triggered
- **Strategy**: Target young professionals with convenience lever, emphasize co-working + downtown access
- **Competitive Advantage**: Rooftop amenities, tech-friendly features vs Downtown Lofts

### Downtown Modern Lofts  
- **Challenge**: Penthouse occupancy at 92% (lower than expected)
- **Strategy**: Target creative professionals + lifestyle positioning
- **Competitive Advantage**: Artist community, gallery spaces, cultural events

### Suburban Family Communities
- **Challenge**: Highest vacancy overall (91.2%), especially 3-bed units
- **Strategy**: Aggressive family-focused campaigns, back-to-school messaging
- **Competitive Advantage**: School district, affordability, spacious units

## Next Steps

1. **Test Campaign Strategist Agent**: Run with campaign_strategist_mock_data inputs
2. **Visual Poster Generation**: Feed campaign briefs to visual_creator with mock_database images
3. **Performance Tracking**: Log impressions, leads, conversions per brief
4. **Optimization Loop**: Update performance history → inform next cycle's strategy

---

**Last Updated**: May 26, 2026
**Framework Version**: 2.0 Real Estate Marketing
