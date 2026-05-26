from leafmesh import LeafMeshLogger, pre_compose
import json
import os
from pathlib import Path
from typing import Dict, Any, List

logger = LeafMeshLogger(__name__)

def generate_poster_html(poster_spec: Dict[str, Any], ratio_type: str, image_url: str = None) -> str:
    """
    Generate HTML for a poster design based on specifications.
    
    Args:
        poster_spec: Poster specification dictionary
        ratio_type: 'desktop' (16:9), 'mobile' (4:5), or 'office' (3:4)
        image_url: URL to the property image to embed
    
    Returns:
        HTML string for the poster
    """
    dimensions = {
        'desktop': {'width': 1920, 'height': 1080, 'name': 'Desktop 16:9'},
        'mobile': {'width': 1080, 'height': 1350, 'name': 'Mobile 4:5'},
        'office': {'width': 1200, 'height': 1600, 'name': 'Office 3:4'}
    }
    
    dims = dimensions[ratio_type]
    colors = poster_spec.get('color_palette', ['#2D5016', '#F4E4C1', '#FFFFFF'])
    headline = poster_spec.get('headline', 'Welcome Home')
    subheadline = poster_spec.get('subheadline', 'Find your perfect apartment')
    cta = poster_spec.get('call_to_action', 'Schedule a Tour')
    
    # Use provided image URL or fallback
    if not image_url:
        image_url = poster_spec.get('photo_selected', 'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=1280&q=80')
    
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Apartment Marketing Poster</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background-color: #f5f5f5;
        }}
        .poster {{
            width: {dims['width']}px;
            height: {dims['height']}px;
            background: linear-gradient(135deg, {colors[0]} 0%, {colors[1]} 100%);
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            align-items: center;
            padding: 40px;
        }}
        .poster-top {{
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            border-radius: 15px;
            overflow: hidden;
            max-height: 50%;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }}
        .poster-top img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        .poster-middle {{
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            width: 100%;
            margin: 30px 0;
        }}
        .headline {{
            font-size: {56 if ratio_type == 'desktop' else 48 if ratio_type == 'mobile' else 52}px;
            font-weight: 900;
            color: #FFFFFF;
            text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.3);
            margin-bottom: 15px;
            line-height: 1.2;
        }}
        .subheadline {{
            font-size: {32 if ratio_type == 'desktop' else 24 if ratio_type == 'mobile' else 28}px;
            font-weight: 500;
            color: rgba(255, 255, 255, 0.9);
            text-shadow: 1px 1px 4px rgba(0, 0, 0, 0.2);
            margin-bottom: 30px;
            line-height: 1.3;
        }}
        .poster-bottom {{
            flex-shrink: 0;
            width: 100%;
            display: flex;
            justify-content: center;
        }}
        .cta-button {{
            background-color: {colors[2]};
            color: {colors[0]};
            padding: 18px 50px;
            font-size: {24 if ratio_type == 'desktop' else 20}px;
            font-weight: bold;
            border: none;
            border-radius: 50px;
            cursor: pointer;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
            transition: transform 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .cta-button:hover {{
            transform: scale(1.05);
        }}
        .ratio-info {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(0, 0, 0, 0.5);
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="poster">
        <div class="ratio-info">{dims['name']} ({dims['width']}x{dims['height']}px)</div>
        
        <div class="poster-top">
            <img src="{image_url}" alt="Property Image" />
        </div>
        
        <div class="poster-middle">
            <h1 class="headline">{headline}</h1>
            <p class="subheadline">{subheadline}</p>
        </div>
        
        <div class="poster-bottom">
            <button class="cta-button">{cta}</button>
        </div>
    </div>
</body>
</html>
"""
    return html


async def html_to_png_async(html_content: str, output_path: str, width: int, height: int) -> bool:
    """
    Convert HTML string to PNG file using Playwright (async version).
    
    Args:
        html_content: HTML string
        output_path: Path to save PNG file
        width: Desired width
        height: Desired height
    
    Returns:
        True if successful, False otherwise
    """
    try:
        from playwright.async_api import async_playwright
        import tempfile
        
        # Write HTML to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html_content)
            temp_html = f.name
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": width, "height": height})
            await page.goto(f"file://{temp_html}")
            await page.screenshot(path=output_path)
            await browser.close()
        
        # Clean up
        if os.path.exists(temp_html):
            os.remove(temp_html)
        
        logger.info(f"  ✓ PNG created: {Path(output_path).name}")
        return True
        
    except ImportError:
        logger.warning("Playwright not available, HTML-only mode")
        return False
    except Exception as e:
        logger.error(f"Error converting HTML to PNG: {e}")
        return False


@pre_compose()
async def visual_creator(llm_response, input_data, context):
    """
    Visual Creator Agent - Generates HTML-based poster designs in multiple aspect ratios
    and exports them as PNG images.
    """
    logger.info("🎨 Visual Creator Agent Starting...")
    
    # Parse inputs
    campaign_briefs_json = input_data.get("campaign_briefs", "[]")
    briefs_count = input_data.get("briefs_count", 0)
    property_photos_json = input_data.get("property_photos", "[]")
    amenity_list_json = input_data.get("amenity_list", "[]")
    
    try:
        campaign_briefs = json.loads(campaign_briefs_json) if isinstance(campaign_briefs_json, str) else campaign_briefs_json
        property_photos = json.loads(property_photos_json) if isinstance(property_photos_json, str) else property_photos_json
        amenity_list = json.loads(amenity_list_json) if isinstance(amenity_list_json, str) else amenity_list_json
    except:
        campaign_briefs = []
        property_photos = []
        amenity_list = []
    
    logger.info(f"Processing {briefs_count} briefs with {len(property_photos)} photos")
    
    # Create output directory
    output_dir = Path('/Users/bhumkamehndiratta/Desktop/Leafcraft/NewSocialMedia/SocialMediaMarketing_v2/generated_posters')
    output_dir.mkdir(exist_ok=True)
    
    # Generate poster designs for each brief in 3 aspect ratios
    poster_designs = []
    poster_files_saved = 0
    ratio_types = ['desktop', 'mobile', 'office']
    
    for i, brief in enumerate(campaign_briefs[:3], 1):
        persona = brief.get('renter_persona', 'General')
        lever = brief.get('emotional_lever', 'convenience')
        floorplan = brief.get('target_floorplan', 'Unknown')
        
        # Define color palettes based on emotional lever
        color_palettes = {
            'move_in_ease': ['#2D5016', '#F4E4C1', '#FFFFFF'],      # Warm green/cream
            'convenience': ['#1A1A2E', '#0F3460', '#E94560'],        # Modern dark blue
            'affordability': ['#F39C12', '#FFFFFF', '#2C3E50'],      # Bright orange
        }
        
        colors = color_palettes.get(lever, ['#2D5016', '#F4E4C1', '#FFFFFF'])
        
        # Base poster specification for this brief
        poster_spec = {
            "poster_id": f"poster_{i:03d}",
            "brief_id": brief.get('brief_id', f'brief_{i:03d}'),
            "name": f"{persona.title()} - {floorplan}",
            "target_persona": persona,
            "target_floorplan": floorplan,
            "emotional_lever": lever,
            "color_palette": colors,
            "headline": f"{persona.title()} Love Living Here" if lever == "move_in_ease" else (
                f"Your {floorplan} Awaits You" if lever == "convenience" else
                f"Luxury Doesn't Have to Break the Bank"
            ),
            "subheadline": brief.get('messaging_direction', 'Perfect for your lifestyle')[:80],
            "call_to_action": "Schedule a Tour" if lever != "affordability" else "Get Your Quote Today",
            "amenities": amenity_list[:3] if amenity_list else ["Modern amenities", "Community spaces"],
            "photo_selected": property_photos[0].get('url', 'photo1.jpg') if property_photos else 'photo1.jpg',
            "ratios_generated": ratio_types,
            "files_created": []
        }
        
        # Generate posters in 3 different aspect ratios
        for ratio_type in ratio_types:
            # Get image from property_photos or use a default
            image_url = None
            if input_data.get('property_photos') and len(input_data['property_photos']) > 0:
                image_url = input_data['property_photos'][0].get('url', None)
            
            # Generate HTML with image
            html_content = generate_poster_html(poster_spec, ratio_type, image_url)
            
            # Save HTML file
            html_filename = f"poster_{i:03d}_{ratio_type}.html"
            html_filepath = output_dir / html_filename
            with open(html_filepath, 'w') as f:
                f.write(html_content)
            poster_spec["files_created"].append(str(html_filepath))
            
            # Try to convert to PNG
            png_filename = f"poster_{i:03d}_{ratio_type}.png"
            png_filepath = output_dir / png_filename
            await html_to_png_async(html_content, str(png_filepath), 1920 if ratio_type == 'desktop' else 1080, 1080 if ratio_type == 'desktop' else 1350)
            poster_spec["files_created"].append(str(png_filepath))
            poster_files_saved += 1
        
        poster_designs.append(poster_spec)
        logger.info(f"  ✓ Poster {i} created for {persona} with 3 aspect ratios")
    
    # Return results
    result = {
        "visual_packages": json.dumps(poster_designs),
        "briefs_covered": len(poster_designs),
        "formats_produced": json.dumps(ratio_types),
        "poster_files_saved": poster_files_saved,
    }
    
    logger.info(f"✨ Visual Creator completed: {len(poster_designs)} posters in {len(ratio_types)} formats = {poster_files_saved} files")
    logger.info(f"📁 Posters saved to: {output_dir}")
    
    return result
