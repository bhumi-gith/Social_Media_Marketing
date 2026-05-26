from html import escape as html_escape
from leafmesh import LeafMeshLogger, pre_compose
import asyncio
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List

logger = LeafMeshLogger(__name__)

# ─── Platform dimensions ──────────────────────────────────────────────────────
DIMENSIONS = {
    "instagram_square":   {"width": 1080, "height": 1080, "label": "Instagram 1:1"},
    "instagram_portrait": {"width": 1080, "height": 1350, "label": "Instagram 4:5"},
    "facebook_post":      {"width": 1200, "height": 630,  "label": "Facebook Post"},
}

_FONTS_BASE = {
    "instagram_square":   {"headline": 54, "subheadline": 26, "body": 15, "label": 13, "cta": 17},
    "instagram_portrait": {"headline": 58, "subheadline": 28, "body": 16, "label": 14, "cta": 18},
    "facebook_post":      {"headline": 46, "subheadline": 22, "body": 13, "label": 12, "cta": 15},
}

# Fixed section heights
_LOGO_H    = {"instagram_square": 54,  "instagram_portrait": 60,  "facebook_post": 46}
_GALLERY_H = {"instagram_square": 210, "instagram_portrait": 260, "facebook_post": 110}
_ABOUT_H   = {"instagram_square": 130, "instagram_portrait": 160, "facebook_post": 0}
_FOOTER_H  = {"instagram_square": 105, "instagram_portrait": 115, "facebook_post": 72}
_PAD       = {"instagram_square": 38,  "instagram_portrait": 50,  "facebook_post": 30}

# Beige used for HOME FEATURES box and ABOUT section — constant across all levers
_BEIGE     = "#EDE8DF"
_BEIGE_DRK = "#D8D0C4"

FALLBACK_IMAGE = "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=1280&q=80"

# ─── Professional lever themes ────────────────────────────────────────────────
# primary  = dark neutral used for logo bar, price block, footer, decorative accents
# accent   = single gold used for rules, labels, CTA buttons
# card_bg  = white/near-white for text panels
# text_dark / text_muted = typography hierarchy
GOLD = "#B8962E"

LEVER_THEMES: Dict[str, Dict[str, str]] = {
    "move_in_ease": {
        "primary":         "#1C3A2A",
        "accent":          GOLD,
        "card_bg":         "#FFFFFF",
        "text_on_primary": "#F0EDE6",
        "text_dark":       "#1A1A1A",
        "text_muted":      "#6B6860",
        "border":          "#D8D2C8",
        "headline":        "Move In This Weekend — No Surprises",
        "cta":             "Schedule a Viewing",
    },
    "convenience": {
        "primary":         "#1B2B4B",
        "accent":          GOLD,
        "card_bg":         "#FFFFFF",
        "text_on_primary": "#F0EDE6",
        "text_dark":       "#1A1A1A",
        "text_muted":      "#636873",
        "border":          "#CDD4DC",
        "headline":        "Walk to Everything. Live Smarter.",
        "cta":             "Schedule a Tour",
    },
    "affordability": {
        "primary":         "#2D3B45",
        "accent":          GOLD,
        "card_bg":         "#FFFFFF",
        "text_on_primary": "#F0EDE6",
        "text_dark":       "#1A1A1A",
        "text_muted":      "#6B6860",
        "border":          "#D0C9BE",
        "headline":        "Quality Living at an Honest Price",
        "cta":             "Get Your Quote Today",
    },
    "luxury": {
        "primary":         "#111111",
        "accent":          GOLD,
        "card_bg":         "#FAF8F3",
        "text_on_primary": GOLD,
        "text_dark":       "#111111",
        "text_muted":      "#666666",
        "border":          "#D4C99A",
        "headline":        "Where Exceptional Living Begins",
        "cta":             "Request a Private Showing",
    },
    "community": {
        "primary":         "#1A3D4F",
        "accent":          GOLD,
        "card_bg":         "#FFFFFF",
        "text_on_primary": "#F0EDE6",
        "text_dark":       "#1A1A1A",
        "text_muted":      "#5E6E78",
        "border":          "#C0CDD8",
        "headline":        "More Than an Apartment. A Community.",
        "cta":             "Join Our Community",
    },
    "lifestyle": {
        "primary":         "#252B2B",
        "accent":          GOLD,
        "card_bg":         "#FFFFFF",
        "text_on_primary": "#F0EDE6",
        "text_dark":       "#1A1A1A",
        "text_muted":      "#6B6860",
        "border":          "#CCCAC4",
        "headline":        "Live Where the Action Is",
        "cta":             "Explore the Lifestyle",
    },
    "urgency": {
        "primary":         "#3B1F2B",
        "accent":          GOLD,
        "card_bg":         "#FFFFFF",
        "text_on_primary": "#F0EDE6",
        "text_dark":       "#1A1A1A",
        "text_muted":      "#6B6060",
        "border":          "#CEBEC4",
        "headline":        "Limited Availability — Reserve Your Home Today",
        "cta":             "Reserve Now",
    },
    "family_safety": {
        "primary":         "#1F2D3D",
        "accent":          GOLD,
        "card_bg":         "#FFFFFF",
        "text_on_primary": "#F0EDE6",
        "text_dark":       "#1A1A1A",
        "text_muted":      "#5E6670",
        "border":          "#C4CCD8",
        "headline":        "Safe. Spacious. Everything Your Family Needs.",
        "cta":             "Book a Family Tour",
    },
}

_FALLBACK_LEVER = "convenience"

# ─── Data helpers ─────────────────────────────────────────────────────────────

def _fonts(ratio_type: str) -> Dict[str, int]:
    return _FONTS_BASE.get(ratio_type, _FONTS_BASE["instagram_portrait"])


def _parse_input(raw: Any, fallback: Any) -> Any:
    try:
        result = json.loads(raw) if isinstance(raw, str) else raw
        return result if result is not None else fallback
    except Exception:
        return fallback


_NUM_WORDS = {"1": "one", "2": "two", "3": "three", "4": "four", "5": "five"}

def _extract_price(pricing_data: Any, floorplan: str) -> str:
    try:
        pricing = _parse_input(pricing_data, {})
        if isinstance(pricing, dict):
            fl = floorplan.lower()
            m = re.search(r'\d', fl)
            candidates = {fl}
            if m:
                d = m.group(); w = _NUM_WORDS.get(d, d)
                candidates.update({d, w, f"{w}_bedroom", f"{w}br", f"{d}-bedroom", f"{d}br", f"{w} bedroom"})
            for key, val in pricing.items():
                k = key.lower()
                if any(c in k or k in c for c in candidates):
                    return str(val)
            return str(next(iter(pricing.values()))) if pricing else "Contact for Pricing"
    except Exception:
        pass
    return "Contact for Pricing"


def _extract_beds_baths(floorplan: str) -> Dict[str, str]:
    fl = floorplan.lower()
    if "studio" in fl:
        return {"beds": "Studio", "baths": "1 Bath"}
    m = re.search(r'(\d)', fl)
    if m:
        n = int(m.group(1))
        return {"beds": f"{n} Bed", "baths": f"{min(n,2)} Bath"}
    return {"beds": "—", "baths": "—"}


def _extract_sqft(sqft_map: Any, floorplan: str) -> str:
    try:
        data = _parse_input(sqft_map, {})
        if isinstance(data, dict):
            fl = floorplan.lower()
            m = re.search(r'\d', fl)
            candidates = {fl}
            if m:
                d = m.group(); w = _NUM_WORDS.get(d, d)
                candidates.update({d, w, f"{w}_bedroom", f"{d}-bedroom", f"{w} bedroom"})
            for key, val in data.items():
                if any(c in key.lower() or key.lower() in c for c in candidates):
                    return str(val)
    except Exception:
        pass
    return ""


def _build_room_photos(property_photos: List[Dict], hero_idx: int) -> List[Dict[str, str]]:
    rooms = [p for i, p in enumerate(property_photos) if i != hero_idx][:3]
    result = []
    for room in rooms:
        caption = room.get("caption") or (room.get("tags", [""])[0] if room.get("tags") else "Room")
        result.append({"url": room.get("url", FALLBACK_IMAGE), "label": str(caption).upper()[:20]})
    defaults = ["LIVING AREA", "BEDROOM", "AMENITIES"]
    while len(result) < 3:
        result.append({"url": FALLBACK_IMAGE, "label": defaults[len(result)]})
    return result


def _checklist_max(ratio_type: str) -> int:
    return {"instagram_portrait": 6, "instagram_square": 5, "facebook_post": 4}.get(ratio_type, 5)


# ─── SVG icons & decorative elements ─────────────────────────────────────────

_BED_D   = "M20 9V7c0-1.1-.9-2-2-2H6c-1.1 0-2 .9-2 2v2c-1.1 0-2 .9-2 2v5h1.33L4 18h1l.67-2h12.67l.66 2h1l.67-2H22v-5c0-1.1-.9-2-2-2zm-12 0V7h4v2H8zm6 0V7h4v2h-4z"
_BATH_D  = "M7 11h2v2H7zm0 4h2v2H7zm4-4h2v2h-2zm0 4h2v2h-2zm4-4h2v2h-2zm0 4h2v2h-2zM20 13H4V7c0-1.1.9-2 2-2s2 .9 2 2h2c0-1.1.9-2 2-2s2 .9 2 2h2c0-1.1.9-2 2-2s2 .9 2 2v6zm0 2v4H4v-4h16z"
_SQFT_D  = "M21 3L3 21l1.41 1.41 2.79-2.79V21h2v-5.59l11-11V21h2V3h-1.41zM3 3v2h.59L3 6.59V3z"
_PHONE_D = "M6.6 10.8c1.4 2.8 3.8 5.1 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1-9.4 0-17-7.6-17-17 0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1L6.6 10.8z"
_PIN_D   = "M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"
_GLOB_D  = "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"

def _svg(path_d: str, size: int, color: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
            f'viewBox="0 0 24 24" fill="{color}" style="flex-shrink:0"><path d="{path_d}"/></svg>')


def _qr_svg(size: int) -> str:
    """Decorative QR-code-like SVG placeholder."""
    c, w, s = "#1A1A1A", "white", size
    b = 4  # border
    return f'''<svg width="{s}" height="{s}" viewBox="0 0 {s} {s}" xmlns="http://www.w3.org/2000/svg">
  <rect width="{s}" height="{s}" fill="white"/>
  <rect x="{b}" y="{b}" width="36" height="36" fill="{c}" rx="2"/>
  <rect x="{b+6}" y="{b+6}" width="24" height="24" fill="{w}"/>
  <rect x="{b+10}" y="{b+10}" width="16" height="16" fill="{c}"/>
  <rect x="{s-b-36}" y="{b}" width="36" height="36" fill="{c}" rx="2"/>
  <rect x="{s-b-30}" y="{b+6}" width="24" height="24" fill="{w}"/>
  <rect x="{s-b-26}" y="{b+10}" width="16" height="16" fill="{c}"/>
  <rect x="{b}" y="{s-b-36}" width="36" height="36" fill="{c}" rx="2"/>
  <rect x="{b+6}" y="{s-b-30}" width="24" height="24" fill="{w}"/>
  <rect x="{b+10}" y="{s-b-26}" width="16" height="16" fill="{c}"/>
  <rect x="46" y="{b+4}" width="6" height="6" fill="{c}"/>
  <rect x="54" y="{b+4}" width="6" height="6" fill="{c}"/>
  <rect x="46" y="{b+12}" width="6" height="10" fill="{c}"/>
  <rect x="54" y="{b+14}" width="10" height="6" fill="{c}"/>
  <rect x="{b+4}" y="46" width="10" height="6" fill="{c}"/>
  <rect x="{b+16}" y="46" width="6" height="10" fill="{c}"/>
  <rect x="{b+4}" y="54" width="6" height="6" fill="{c}"/>
  <rect x="46" y="46" width="10" height="6" fill="{c}"/>
  <rect x="46" y="54" width="6" height="10" fill="{c}"/>
</svg>'''


# ─── Shared UI components ─────────────────────────────────────────────────────

def _logo_bar_html(property_name: str, status: str, theme: Dict, ratio_type: str) -> str:
    lh  = _LOGO_H[ratio_type]
    f   = _fonts(ratio_type)
    pad = _PAD[ratio_type]
    return (
        f'<div style="flex:0 0 {lh}px;display:flex;align-items:center;justify-content:space-between;'
        f'padding:0 {pad}px;background:{theme["primary"]}">'
        f'<span style="font-size:{f["label"]+3}px;font-weight:700;color:{theme["text_on_primary"]};'
        f'letter-spacing:2px;text-transform:uppercase;font-family:Georgia,serif">'
        f'{html_escape(property_name)}</span>'
        f'<span style="background:{theme["accent"]};color:#111111;padding:4px 16px;'
        f'font-size:{f["label"]-1}px;font-weight:700;text-transform:uppercase;letter-spacing:2px;border-radius:2px">'
        f'{html_escape(status)}</span>'
        f'</div>'
    )


def _specs_row_html(beds: str, baths: str, sqft: str, theme: Dict, ratio_type: str) -> str:
    """Horizontal bed/bath/sqft row with SVG icons."""
    f   = _fonts(ratio_type)
    px  = f["label"] + 1
    ic  = f["label"] + 3
    div = f'<span style="color:{_BEIGE_DRK};margin:0 12px">|</span>'

    def item(d: str, val: str) -> str:
        return (f'<span style="display:inline-flex;align-items:center;gap:5px">'
                f'{_svg(d, ic, theme["accent"])}'
                f'<span style="font-size:{px}px;color:{theme["text_dark"]};font-weight:600">'
                f'{html_escape(val)}</span></span>')

    parts = item(_BED_D, beds) + div + item(_BATH_D, baths)
    if sqft:
        parts += div + item(_SQFT_D, sqft)
    return f'<div style="display:flex;align-items:center">{parts}</div>'


def _features_box_html(amenities: List[str], theme: Dict, ratio_type: str, max_items: int = 6) -> str:
    """Beige box with HOME FEATURES heading and bullet list — reference style."""
    f      = _fonts(ratio_type)
    px     = f["label"] + 1
    mb     = 8 if ratio_type == "instagram_portrait" else 6
    pad    = {"instagram_portrait": 20, "instagram_square": 16, "facebook_post": 12}.get(ratio_type, 16)
    rows   = "".join(
        f'<div style="display:flex;align-items:flex-start;gap:9px;margin-bottom:{mb}px">'
        f'<span style="color:{theme["accent"]};font-size:{px+2}px;line-height:1.3;flex-shrink:0;font-weight:700">•</span>'
        f'<span style="font-size:{px}px;color:{theme["text_dark"]};line-height:1.4">{html_escape(str(a))}</span>'
        f'</div>'
        for a in amenities[:max_items]
    )
    return (
        f'<div style="background:{_BEIGE};padding:{pad}px;border-left:3px solid {theme["accent"]}">'
        f'<div style="font-size:{f["label"]}px;font-weight:700;color:{theme["text_dark"]};'
        f'text-transform:uppercase;letter-spacing:2px;margin-bottom:{pad//2}px">'
        f'Home Features</div>'
        f'{rows}'
        f'</div>'
    )


def _price_block_html(pricing: str, theme: Dict, ratio_type: str) -> str:
    """Dark primary block with START PRICE label — reference style."""
    f      = _fonts(ratio_type)
    big_px = {"instagram_portrait": 48, "instagram_square": 44, "facebook_post": 36}.get(ratio_type, 44)
    pad    = {"instagram_portrait": 20, "instagram_square": 16, "facebook_post": 12}.get(ratio_type, 16)
    return (
        f'<div style="background:{theme["primary"]};padding:{pad}px {pad+8}px;display:inline-flex;'
        f'flex-direction:column;gap:2px">'
        f'<span style="font-size:{f["label"]-1}px;color:{theme["accent"]};font-weight:700;'
        f'text-transform:uppercase;letter-spacing:2px">Start Price</span>'
        f'<span style="font-size:{big_px}px;font-weight:700;color:#FFFFFF;line-height:1.0;'
        f'font-family:Georgia,serif">{html_escape(pricing)}</span>'
        f'<span style="font-size:{f["label"]-1}px;color:rgba(255,255,255,.65);letter-spacing:.5px">per month</span>'
        f'</div>'
    )


def _discount_html(concession: str, theme: Dict, ratio_type: str) -> str:
    """Prominent concession/discount callout — reference style."""
    f = _fonts(ratio_type)
    # Extract a percentage if present, otherwise show text in a block
    pct_match = re.search(r'(\d+)\s*%', concession)
    if pct_match:
        pct = pct_match.group(1)
        label = re.sub(r'\d+\s*%\s*', '', concession).strip() or "Discount"
        return (
            f'<div style="display:flex;flex-direction:column;align-items:center;justify-content:center">'
            f'<span style="font-size:{f["headline"]-4}px;font-weight:900;color:{theme["primary"]};'
            f'line-height:1.0;font-family:Georgia,serif">{pct}%</span>'
            f'<span style="font-size:{f["label"]}px;font-weight:700;color:{theme["text_muted"]};'
            f'text-transform:uppercase;letter-spacing:1.5px">{html_escape(label)}</span>'
            f'</div>'
        )
    # Non-percentage concession — show in accent-bordered box
    pad = 12 if ratio_type == "facebook_post" else 16
    return (
        f'<div style="border:2px solid {theme["accent"]};padding:{pad}px;display:flex;'
        f'flex-direction:column;gap:3px">'
        f'<span style="font-size:{f["label"]-1}px;font-weight:700;color:{theme["accent"]};'
        f'text-transform:uppercase;letter-spacing:2px">Special Offer</span>'
        f'<span style="font-size:{f["body"]}px;color:{theme["text_dark"]};line-height:1.4">'
        f'{html_escape(concession)}</span>'
        f'</div>'
    )


def _gallery3_html(room_photos: List[Dict], theme: Dict, ratio_type: str) -> str:
    """Three equal-width room photos side by side — reference style."""
    gh    = _GALLERY_H[ratio_type]
    gap   = {"instagram_portrait": 6, "instagram_square": 6, "facebook_post": 4}.get(ratio_type, 6)
    f     = _fonts(ratio_type)
    lbl_h = {"instagram_portrait": 32, "instagram_square": 28, "facebook_post": 22}.get(ratio_type, 28)
    photos = "".join(
        f'<div style="flex:1;display:flex;flex-direction:column;overflow:hidden">'
        f'<div style="flex:1;min-height:0;background:url(\'{html_escape(r["url"])}\') center/cover no-repeat"></div>'
        f'<div style="flex:0 0 {lbl_h}px;background:{theme["primary"]};color:{theme["text_on_primary"]};'
        f'display:flex;align-items:center;justify-content:center;'
        f'font-size:{f["label"]-1}px;font-weight:600;text-transform:uppercase;letter-spacing:1.5px">'
        f'{html_escape(r["label"])}</div>'
        f'</div>'
        for r in room_photos[:3]
    )
    return (
        f'<div style="flex:0 0 {gh}px;display:flex;gap:{gap}px;background:#111111">'
        f'{photos}</div>'
    )


def _about_section_html(about_text: str, theme: Dict, ratio_type: str) -> str:
    """Beige band with centered ABOUT THIS PROPERTY heading + text."""
    ah  = _ABOUT_H[ratio_type]
    if ah == 0:
        return ""
    f   = _fonts(ratio_type)
    pad = _PAD[ratio_type]
    return (
        f'<div style="flex:0 0 {ah}px;background:{_BEIGE};display:flex;flex-direction:column;'
        f'align-items:center;justify-content:center;padding:{pad//2}px {pad}px;gap:8px;'
        f'border-top:1px solid {_BEIGE_DRK}">'
        f'<div style="font-size:{f["label"]+1}px;font-weight:700;color:{theme["text_dark"]};'
        f'text-transform:uppercase;letter-spacing:2.5px;font-family:Georgia,serif">'
        f'About This Property</div>'
        f'<div style="font-size:{f["body"]}px;color:{theme["text_muted"]};line-height:1.7;'
        f'text-align:center;max-width:82%">{html_escape(about_text)}</div>'
        f'</div>'
    )


def _footer_html(phone: str, website: str, address: str, property_name: str, theme: Dict, ratio_type: str) -> str:
    """Dark footer with circular brand logo + QR code + contact columns — reference style."""
    fh     = _FOOTER_H[ratio_type]
    pad    = _PAD[ratio_type]
    f      = _fonts(ratio_type)
    qr_sz  = {"instagram_portrait": 68, "instagram_square": 60, "facebook_post": 44}.get(ratio_type, 60)
    ico_sz = f["label"] + 2
    circ   = {"instagram_portrait": 52, "instagram_square": 46, "facebook_post": 36}.get(ratio_type, 46)

    # Circular brand logo
    brand_html = (
        f'<div style="display:flex;align-items:center;gap:12px">'
        f'<div style="width:{circ}px;height:{circ}px;border-radius:50%;background:{theme["accent"]};'
        f'display:flex;align-items:center;justify-content:center;flex-shrink:0">'
        f'<span style="font-size:{circ//2}px;font-weight:900;color:#111111;font-family:Georgia,serif">R</span>'
        f'</div>'
        f'<div style="display:flex;flex-direction:column;gap:1px">'
        f'<span style="font-size:{f["label"]+1}px;font-weight:700;color:{theme["text_on_primary"]};'
        f'text-transform:uppercase;letter-spacing:1.5px">{html_escape(property_name)}</span>'
        f'<span style="font-size:{f["label"]-2}px;color:rgba(255,255,255,.55);letter-spacing:.5px">'
        f'{html_escape(website)}</span>'
        f'</div></div>'
    )

    # QR code
    qr_html = (
        f'<div style="display:flex;flex-direction:column;align-items:center;gap:3px">'
        f'{_qr_svg(qr_sz)}'
        f'<span style="font-size:{f["label"]-3}px;color:rgba(255,255,255,.45);letter-spacing:.5px">Scan QR</span>'
        f'</div>'
    )

    def contact_item(d: str, text: str) -> str:
        return (f'<div style="display:flex;align-items:center;gap:5px">'
                f'{_svg(d, ico_sz, theme["accent"])}'
                f'<span style="font-size:{f["label"]}px;color:rgba(255,255,255,.88)">{html_escape(text)}</span>'
                f'</div>')

    contact_html = (
        f'<div style="display:flex;flex-direction:column;gap:5px">'
        f'{contact_item(_PHONE_D, phone)}'
        f'{contact_item(_PIN_D, address) if address else ""}'
        f'{contact_item(_GLOB_D, website)}'
        f'</div>'
    )

    return (
        f'<div style="flex:0 0 {fh}px;display:flex;align-items:center;justify-content:space-between;'
        f'padding:0 {pad}px;background:{theme["primary"]};border-top:3px solid {theme["accent"]}">'
        f'{brand_html}{qr_html}{contact_html}'
        f'</div>'
    )


# ─── Template helpers for hero content ────────────────────────────────────────

def _cta_button_html(cta: str, theme: Dict, ratio_type: str) -> str:
    f   = _fonts(ratio_type)
    py  = {"instagram_portrait": 14, "instagram_square": 12, "facebook_post": 9}.get(ratio_type, 12)
    px  = {"instagram_portrait": 40, "instagram_square": 34, "facebook_post": 24}.get(ratio_type, 34)
    return (
        f'<div style="display:inline-block;background:{theme["accent"]};color:#111111;'
        f'padding:{py}px {px}px;font-size:{f["cta"]}px;font-weight:700;'
        f'text-transform:uppercase;letter-spacing:2px;border-radius:2px;cursor:pointer">'
        f'{html_escape(cta)}</div>'
    )


# ─── Shared poster wrapper ─────────────────────────────────────────────────────
# All templates compose: logo_bar + hero_section + gallery3 + about + footer
# The only difference between templates is the HERO SECTION layout.
# TEXT IS NEVER PLACED OVER IMAGES — all text lives in white/beige panels.

def _build_poster(
    hero_html: str,
    spec: Dict,
    theme: Dict,
    ratio_type: str,
    image_url: str,
) -> str:
    d       = DIMENSIONS[ratio_type]
    logo    = _logo_bar_html(spec.get("property_name", "Property"), spec.get("availability_status", "For Rent"), theme, ratio_type)
    gallery = _gallery3_html(spec.get("room_photos", []), theme, ratio_type)
    about   = _about_section_html(spec.get("about_text", ""), theme, ratio_type)
    footer  = _footer_html(
        spec.get("contact_phone", ""), spec.get("contact_website", ""),
        spec.get("contact_address", ""), spec.get("property_name", "Property"),
        theme, ratio_type,
    )
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>Poster</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#FFFFFF}}
.poster{{width:{d['width']}px;height:{d['height']}px;display:flex;flex-direction:column;overflow:hidden;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;background:#FFFFFF}}
</style></head><body>
<div class="poster">
  {logo}
  {hero_html}
  {gallery}
  {about}
  {footer}
</div></body></html>"""


# ─── Template 1: Classic Two-Column (Text Left / Image Right) ─────────────────
# White panel left: gold bar, headline, specs, features box, price+discount.
# Clean image right. Reference-inspired layout, emphasis on specs.

def template_hero_overlay(spec: Dict, ratio_type: str, image_url: str, theme: Dict) -> str:
    f          = _fonts(ratio_type)
    pad        = _PAD[ratio_type]
    headline   = html_escape(spec.get("headline", "Welcome Home"))
    sub        = html_escape(spec.get("subheadline", ""))
    pricing    = spec.get("pricing_info", "Contact for Pricing")
    beds       = spec.get("bedrooms", "—")
    baths      = spec.get("bathrooms", "—")
    sqft       = spec.get("sq_footage", "")
    amenities  = spec.get("amenities", [])
    concession = spec.get("concession_details", "")
    max_items  = _checklist_max(ratio_type)
    is_land    = ratio_type == "facebook_post"
    img_w      = "52%" if is_land else "55%"
    fdir       = "row" if is_land else "row"
    gap        = {"instagram_portrait": 18, "instagram_square": 16, "facebook_post": 12}.get(ratio_type, 16)

    specs_row = _specs_row_html(beds, baths, sqft, theme, ratio_type)
    feat_box  = _features_box_html(amenities, theme, ratio_type, max_items)
    price_blk = _price_block_html(pricing, theme, ratio_type)
    cta_btn   = _cta_button_html(spec.get("call_to_action", "Schedule a Tour"), theme, ratio_type)

    price_row = (
        f'<div style="display:flex;align-items:stretch;gap:{gap}px">'
        f'{price_blk}'
        f'{_discount_html(concession, theme, ratio_type) if concession else ""}'
        f'</div>'
    )

    hero = f"""<div style="flex:1;min-height:0;display:flex;flex-direction:{fdir};overflow:hidden">
  <!-- Text panel -->
  <div style="flex:1;display:flex;flex-direction:column;justify-content:center;padding:{pad}px;
    gap:{gap}px;overflow:hidden;background:{theme["card_bg"]};border-right:1px solid {theme["border"]}">
    <div style="width:36px;height:3px;background:{theme["accent"]}"></div>
    <div style="font-size:{f["label"]}px;font-weight:700;color:{theme["accent"]};
      text-transform:uppercase;letter-spacing:2px">
      {html_escape(spec.get("target_floorplan","Apartment"))} &nbsp;·&nbsp; For Rent</div>
    <h1 style="font-size:{f["headline"]}px;font-weight:700;color:{theme["text_dark"]};
      line-height:1.12;font-family:Georgia,serif;margin:0">{headline}</h1>
    {f'<p style="font-size:{f["body"]}px;color:{theme["text_muted"]};line-height:1.65;margin:0;font-style:italic">{sub}</p>' if sub else ""}
    <div style="height:1px;background:{theme["border"]}"></div>
    {specs_row}
    {feat_box}
    {price_row}
    {cta_btn}
  </div>
  <!-- Image panel -->
  <div style="flex:0 0 {img_w};position:relative;overflow:hidden">
    <div style="position:absolute;inset:0;background:url('{html_escape(image_url)}') center/cover no-repeat"></div>
    <div style="position:absolute;bottom:0;left:0;width:40px;height:40px;background:{theme["primary"]}"></div>
  </div>
</div>"""

    return _build_poster(hero, spec, theme, ratio_type, image_url)


# ─── Template 2: Image Left / Info Panel Right ────────────────────────────────
# Image fills the left side. Right white panel: headline, specs, features, price.

def template_split_panel(spec: Dict, ratio_type: str, image_url: str, theme: Dict) -> str:
    f          = _fonts(ratio_type)
    pad        = _PAD[ratio_type]
    headline   = html_escape(spec.get("headline", "Welcome Home"))
    sub        = html_escape(spec.get("subheadline", ""))
    pricing    = spec.get("pricing_info", "Contact for Pricing")
    beds       = spec.get("bedrooms", "—")
    baths      = spec.get("bathrooms", "—")
    sqft       = spec.get("sq_footage", "")
    amenities  = spec.get("amenities", [])
    concession = spec.get("concession_details", "")
    max_items  = _checklist_max(ratio_type)
    is_land    = ratio_type == "facebook_post"
    img_w      = "48%" if is_land else "50%"
    fdir       = "row"
    gap        = {"instagram_portrait": 18, "instagram_square": 16, "facebook_post": 12}.get(ratio_type, 16)

    specs_row = _specs_row_html(beds, baths, sqft, theme, ratio_type)
    feat_box  = _features_box_html(amenities, theme, ratio_type, max_items)
    price_blk = _price_block_html(pricing, theme, ratio_type)
    cta_btn   = _cta_button_html(spec.get("call_to_action", "Schedule a Tour"), theme, ratio_type)

    price_row = (
        f'<div style="display:flex;align-items:stretch;gap:{gap}px">'
        f'{price_blk}'
        f'{_discount_html(concession, theme, ratio_type) if concession else ""}'
        f'</div>'
    )

    hero = f"""<div style="flex:1;min-height:0;display:flex;flex-direction:{fdir};overflow:hidden">
  <!-- Image panel (left) -->
  <div style="flex:0 0 {img_w};position:relative;overflow:hidden">
    <div style="position:absolute;inset:0;background:url('{html_escape(image_url)}') center/cover no-repeat"></div>
    <div style="position:absolute;top:0;right:0;width:40px;height:40px;background:{theme["primary"]}"></div>
  </div>
  <!-- Info panel (right) -->
  <div style="flex:1;display:flex;flex-direction:column;justify-content:center;padding:{pad}px;
    gap:{gap}px;overflow:hidden;background:{theme["card_bg"]};border-left:1px solid {theme["border"]}">
    <div style="width:36px;height:3px;background:{theme["accent"]}"></div>
    <h1 style="font-size:{f["headline"]}px;font-weight:700;color:{theme["text_dark"]};
      line-height:1.12;font-family:Georgia,serif;margin:0">{headline}</h1>
    {f'<p style="font-size:{f["body"]}px;color:{theme["text_muted"]};line-height:1.65;margin:0;font-style:italic">{sub}</p>' if sub else ""}
    <div style="height:1px;background:{theme["border"]}"></div>
    {specs_row}
    {feat_box}
    {price_row}
    {cta_btn}
  </div>
</div>"""

    return _build_poster(hero, spec, theme, ratio_type, image_url)


# ─── Template 3: Image-Top / Content-Bottom ───────────────────────────────────
# Full-width image band (top ~40%). White content zone below:
# headline left, features+price right (two-column within white zone).

def template_bold_statement(spec: Dict, ratio_type: str, image_url: str, theme: Dict) -> str:
    f          = _fonts(ratio_type)
    pad        = _PAD[ratio_type]
    headline   = html_escape(spec.get("headline", "Welcome Home"))
    sub        = html_escape(spec.get("subheadline", ""))
    pricing    = spec.get("pricing_info", "Contact for Pricing")
    beds       = spec.get("bedrooms", "—")
    baths      = spec.get("bathrooms", "—")
    sqft       = spec.get("sq_footage", "")
    amenities  = spec.get("amenities", [])
    concession = spec.get("concession_details", "")
    max_items  = _checklist_max(ratio_type)
    img_h_pct  = "38%" if ratio_type != "facebook_post" else "50%"
    gap        = {"instagram_portrait": 18, "instagram_square": 16, "facebook_post": 12}.get(ratio_type, 16)

    specs_row = _specs_row_html(beds, baths, sqft, theme, ratio_type)
    feat_box  = _features_box_html(amenities, theme, ratio_type, max_items)
    price_blk = _price_block_html(pricing, theme, ratio_type)
    cta_btn   = _cta_button_html(spec.get("call_to_action", "Schedule a Tour"), theme, ratio_type)

    price_row = (
        f'<div style="display:flex;align-items:stretch;gap:{gap}px">'
        f'{price_blk}'
        f'{_discount_html(concession, theme, ratio_type) if concession else ""}'
        f'</div>'
    )

    hero = f"""<div style="flex:1;min-height:0;display:flex;flex-direction:column;overflow:hidden">
  <!-- Full-width image band -->
  <div style="flex:0 0 {img_h_pct};position:relative;overflow:hidden">
    <div style="position:absolute;inset:0;background:url('{html_escape(image_url)}') center/cover no-repeat"></div>
    <div style="position:absolute;bottom:0;left:0;right:0;height:4px;background:{theme["primary"]}"></div>
  </div>
  <!-- Content zone (two columns on white bg) -->
  <div style="flex:1;display:flex;flex-direction:row;background:{theme["card_bg"]};overflow:hidden">
    <!-- Left: headline + specs -->
    <div style="flex:1;display:flex;flex-direction:column;justify-content:center;
      padding:{pad}px;gap:{gap}px;border-right:1px solid {theme["border"]}">
      <div style="width:36px;height:3px;background:{theme["accent"]}"></div>
      <div style="font-size:{f["label"]}px;font-weight:700;color:{theme["accent"]};
        text-transform:uppercase;letter-spacing:2px">
        {html_escape(spec.get("target_floorplan","Apartment"))}</div>
      <h1 style="font-size:{f["headline"]}px;font-weight:700;color:{theme["text_dark"]};
        line-height:1.12;font-family:Georgia,serif;margin:0">{headline}</h1>
      {f'<p style="font-size:{f["body"]}px;color:{theme["text_muted"]};line-height:1.65;margin:0;font-style:italic">{sub}</p>' if sub else ""}
      <div style="height:1px;background:{theme["border"]}"></div>
      {specs_row}
      {cta_btn}
    </div>
    <!-- Right: features + price -->
    <div style="flex:0 0 46%;display:flex;flex-direction:column;justify-content:center;
      padding:{pad}px;gap:{gap}px;overflow:hidden">
      {feat_box}
      {price_row}
    </div>
  </div>
</div>"""

    return _build_poster(hero, spec, theme, ratio_type, image_url)


# ─── Template 4: Reference-Exact Professional Card ────────────────────────────
# Precise recreation of the reference poster:
# White left panel: headline, body text, HOME FEATURES beige box, price block + discount.
# Clean image right with small decorative accent corner.

def template_framed_card(spec: Dict, ratio_type: str, image_url: str, theme: Dict) -> str:
    f          = _fonts(ratio_type)
    pad        = _PAD[ratio_type]
    headline   = html_escape(spec.get("headline", "Welcome Home"))
    sub        = html_escape(spec.get("subheadline", ""))
    desc       = html_escape(spec.get("description_text", ""))
    pricing    = spec.get("pricing_info", "Contact for Pricing")
    beds       = spec.get("bedrooms", "—")
    baths      = spec.get("bathrooms", "—")
    sqft       = spec.get("sq_footage", "")
    amenities  = spec.get("amenities", [])
    concession = spec.get("concession_details", "")
    floorplan  = html_escape(spec.get("target_floorplan", "Apartment"))
    max_items  = _checklist_max(ratio_type)
    is_land    = ratio_type == "facebook_post"
    img_w      = "52%" if is_land else "55%"
    gap        = {"instagram_portrait": 16, "instagram_square": 14, "facebook_post": 10}.get(ratio_type, 14)

    specs_row = _specs_row_html(beds, baths, sqft, theme, ratio_type)
    feat_box  = _features_box_html(amenities, theme, ratio_type, max_items)
    price_blk = _price_block_html(pricing, theme, ratio_type)
    cta_btn   = _cta_button_html(spec.get("call_to_action", "Schedule a Tour"), theme, ratio_type)

    hero = f"""<div style="flex:1;min-height:0;display:flex;flex-direction:row;overflow:hidden">
  <!-- Left text panel — reference layout -->
  <div style="flex:1;display:flex;flex-direction:column;justify-content:center;padding:{pad}px;
    gap:{gap}px;overflow:hidden;background:{theme["card_bg"]}">
    <div style="font-size:{f["label"]+2}px;font-weight:900;color:{theme["text_dark"]};
      text-transform:uppercase;letter-spacing:1px;line-height:1.2;font-family:Georgia,serif">
      {floorplan}<br>
      <span style="color:{theme["primary"]}">For Rent</span>
    </div>
    <div style="width:36px;height:3px;background:{theme["accent"]}"></div>
    {f'<p style="font-size:{f["body"]}px;color:{theme["text_muted"]};line-height:1.65;margin:0">{sub or desc}</p>' if (sub or desc) else ""}
    {specs_row}
    {feat_box}
    <div style="display:flex;align-items:stretch;gap:{gap}px;flex-wrap:wrap">
      {price_blk}
      {_discount_html(concession, theme, ratio_type) if concession else ""}
    </div>
    {f'<p style="font-size:{f["body"]-1}px;color:{theme["text_muted"]};line-height:1.6;margin:0">{html_escape(spec.get("about_text","")[:140])}</p>'}
    {cta_btn}
  </div>
  <!-- Right image — clean, no text overlay -->
  <div style="flex:0 0 {img_w};position:relative;overflow:hidden">
    <div style="position:absolute;inset:0;background:url('{html_escape(image_url)}') center/cover no-repeat"></div>
    <!-- Decorative corner accent (reference detail) -->
    <div style="position:absolute;bottom:0;left:0;width:48px;height:48px;background:{theme["primary"]}"></div>
    <div style="position:absolute;top:0;right:0;width:32px;height:32px;background:{theme["accent"]}"></div>
  </div>
</div>"""

    return _build_poster(hero, spec, theme, ratio_type, image_url)


# ─── Template 5: Dark Panel / Image Right ─────────────────────────────────────
# Dark primary panel fills the left side (no image there).
# All text on dark bg: headline serif white, features reversed (white bullets),
# price large gold serif. Clean image right.

def template_gradient_story(spec: Dict, ratio_type: str, image_url: str, theme: Dict) -> str:
    f          = _fonts(ratio_type)
    pad        = _PAD[ratio_type]
    headline   = html_escape(spec.get("headline", "Welcome Home"))
    sub        = html_escape(spec.get("subheadline", ""))
    pricing    = spec.get("pricing_info", "Contact for Pricing")
    beds       = spec.get("bedrooms", "—")
    baths      = spec.get("bathrooms", "—")
    sqft       = spec.get("sq_footage", "")
    amenities  = spec.get("amenities", [])
    concession = spec.get("concession_details", "")
    floorplan  = html_escape(spec.get("target_floorplan", "Apartment"))
    max_items  = _checklist_max(ratio_type)
    is_land    = ratio_type == "facebook_post"
    img_w      = "50%" if is_land else "52%"
    gap        = {"instagram_portrait": 18, "instagram_square": 16, "facebook_post": 12}.get(ratio_type, 16)
    big_px     = {"instagram_portrait": 48, "instagram_square": 44, "facebook_post": 38}.get(ratio_type, 44)
    mb         = 7 if ratio_type == "facebook_post" else 9

    # Dark-bg feature bullets
    rows = "".join(
        f'<div style="display:flex;align-items:flex-start;gap:9px;margin-bottom:{mb}px">'
        f'<span style="color:{theme["accent"]};font-size:{f["body"]+2}px;line-height:1.3;flex-shrink:0;font-weight:700">—</span>'
        f'<span style="font-size:{f["body"]}px;color:rgba(255,255,255,.85);line-height:1.45">{html_escape(str(a))}</span>'
        f'</div>'
        for a in amenities[:max_items]
    )

    discount_block = (
        f'<div style="border-left:3px solid {theme["accent"]};padding:8px 14px;margin-top:4px">'
        f'<span style="font-size:{f["label"]-1}px;color:{theme["accent"]};font-weight:700;'
        f'text-transform:uppercase;letter-spacing:1.5px">Special Offer</span><br>'
        f'<span style="font-size:{f["body"]}px;color:rgba(255,255,255,.85)">{html_escape(concession)}</span>'
        f'</div>'
    ) if concession else ""

    hero = f"""<div style="flex:1;min-height:0;display:flex;flex-direction:row;overflow:hidden">
  <!-- Dark panel (left) -->
  <div style="flex:1;display:flex;flex-direction:column;justify-content:center;
    padding:{pad}px;gap:{gap}px;overflow:hidden;background:{theme["primary"]}">
    <div style="width:36px;height:3px;background:{theme["accent"]}"></div>
    <div style="font-size:{f["label"]}px;font-weight:700;color:{theme["accent"]};
      text-transform:uppercase;letter-spacing:2px">{floorplan} &nbsp;·&nbsp; For Rent</div>
    <h1 style="font-size:{f["headline"]}px;font-weight:700;color:#FFFFFF;
      line-height:1.12;font-family:Georgia,serif;margin:0">{headline}</h1>
    {f'<p style="font-size:{f["body"]}px;color:rgba(255,255,255,.7);line-height:1.65;margin:0;font-style:italic">{sub}</p>' if sub else ""}
    <div style="height:1px;background:rgba(255,255,255,.15)"></div>
    <!-- Specs on dark -->
    <div style="display:flex;align-items:center;gap:16px">
      <span style="display:inline-flex;align-items:center;gap:5px">
        {_svg(_BED_D, f["label"]+3, theme["accent"])}
        <span style="font-size:{f["label"]+1}px;color:#FFFFFF;font-weight:600">{html_escape(beds)}</span>
      </span>
      <span style="color:rgba(255,255,255,.3)">|</span>
      <span style="display:inline-flex;align-items:center;gap:5px">
        {_svg(_BATH_D, f["label"]+3, theme["accent"])}
        <span style="font-size:{f["label"]+1}px;color:#FFFFFF;font-weight:600">{html_escape(baths)}</span>
      </span>
      {f'<span style="color:rgba(255,255,255,.3)">|</span><span style="font-size:{f["label"]+1}px;color:#FFFFFF;font-weight:600">{html_escape(sqft)}</span>' if sqft else ""}
    </div>
    <!-- Feature list (dark bg) -->
    <div style="display:flex;flex-direction:column">{rows}</div>
    <!-- Price (gold serif, large) -->
    <div style="display:flex;flex-direction:column;gap:2px">
      <span style="font-size:{f["label"]-1}px;color:{theme["accent"]};font-weight:700;
        text-transform:uppercase;letter-spacing:2px">Start Price</span>
      <span style="font-size:{big_px}px;font-weight:700;color:#FFFFFF;line-height:1.0;
        font-family:Georgia,serif">{html_escape(pricing)}</span>
    </div>
    {discount_block}
  </div>
  <!-- Clean image (right) -->
  <div style="flex:0 0 {img_w};position:relative;overflow:hidden">
    <div style="position:absolute;inset:0;background:url('{html_escape(image_url)}') center/cover no-repeat"></div>
    <div style="position:absolute;bottom:0;right:0;width:44px;height:44px;background:{theme["accent"]}"></div>
  </div>
</div>"""

    return _build_poster(hero, spec, theme, ratio_type, image_url)


# ─── Template 6: Blue Hero Poster ────────────────────────────────────────────
# Reference-matched layout:
# TOP (primary-color bg): property name + huge "FOR RENT" headline + dot corner
#   decorations + 3 white-bordered photos + centered white price card.
# BOTTOM (white bg): HOME FEATURES pill badge + 3×2 checkmark grid +
#   description paragraph + rounded pill CTA + two-column circular-icon footer.

def template_blue_hero(spec: Dict, ratio_type: str, image_url: str, theme: Dict) -> str:
    d             = DIMENSIONS[ratio_type]
    f             = _fonts(ratio_type)
    pad           = _PAD[ratio_type]
    property_name = html_escape(spec.get("property_name", "Property"))
    availability  = html_escape(spec.get("availability_status", "For Rent"))
    pricing       = html_escape(spec.get("pricing_info", "Contact for Pricing"))
    amenities     = spec.get("amenities", [])
    cta_text      = html_escape(spec.get("call_to_action", "Book Now"))
    about_text    = html_escape(spec.get("about_text", ""))
    room_photos   = spec.get("room_photos", [])
    phone         = html_escape(spec.get("contact_phone", ""))
    website       = html_escape(spec.get("contact_website", ""))
    concession    = spec.get("concession_details", "")
    subheadline   = html_escape(spec.get("subheadline", ""))

    # Per-ratio sizing
    avail_size  = {"instagram_portrait": 108, "instagram_square": 90, "facebook_post": 58}.get(ratio_type, 90)
    name_size   = {"instagram_portrait": 38,  "instagram_square": 32, "facebook_post": 22}.get(ratio_type, 32)
    price_big   = {"instagram_portrait": 54,  "instagram_square": 46, "facebook_post": 34}.get(ratio_type, 46)
    photo_h     = {"instagram_portrait": 270, "instagram_square": 230, "facebook_post": 130}.get(ratio_type, 230)
    dot_sz      = {"instagram_portrait": 88,  "instagram_square": 76,  "facebook_post": 52}.get(ratio_type, 76)
    gap         = {"instagram_portrait": 14,  "instagram_square": 12,  "facebook_post": 8}.get(ratio_type, 12)
    photo_gap   = {"instagram_portrait": 10,  "instagram_square": 8,   "facebook_post": 5}.get(ratio_type, 8)
    border_w    = 3 if ratio_type != "facebook_post" else 2
    feat_px     = f["body"] + 1
    circ_sz     = f["label"] + 14
    check_icon  = f["label"] + 1

    # Dot-grid corner decoration
    def _dots(sz: int) -> str:
        spacing = sz // 5
        r       = max(2, sz // 28)
        dots    = "".join(
            f'<circle cx="{col*spacing + spacing//2}" cy="{row*spacing + spacing//2}" r="{r}" fill="white" opacity="0.55"/>'
            for row in range(4) for col in range(5)
        )
        return f'<svg width="{sz}" height="{sz//1.25:.0f}" viewBox="0 0 {sz} {int(sz/1.25)}" xmlns="http://www.w3.org/2000/svg">{dots}</svg>'

    # 3 photos with white borders on blue background
    photos_html = "".join(
        f'<div style="flex:1;height:{photo_h}px;border:{border_w}px solid white;overflow:hidden;flex-shrink:0">'
        f'<div style="width:100%;height:100%;background:url(\'{html_escape(r["url"])}\') center/cover no-repeat"></div>'
        f'</div>'
        for r in room_photos[:3]
    )

    # 3×2 checkmark feature grid
    feats = list(amenities[:6])
    while len(feats) < 6:
        feats.append("")
    feat_items = "".join(
        f'<div style="display:flex;align-items:center;gap:8px;flex:0 0 30%;min-width:0">'
        f'<div style="width:{circ_sz}px;height:{circ_sz}px;border-radius:50%;background:{theme["primary"]};'
        f'display:flex;align-items:center;justify-content:center;flex-shrink:0">'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{check_icon}" height="{check_icon}" viewBox="0 0 24 24" fill="white">'
        f'<path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg></div>'
        f'<span style="font-size:{feat_px}px;color:{theme["text_dark"]};font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'
        f'{html_escape(str(a))}</span></div>'
        for a in feats if a
    )

    # Concession line inside price card
    concession_line = (
        f'<div style="font-size:{f["label"]-1}px;color:{theme["accent"]};font-weight:700;'
        f'letter-spacing:1px;margin-top:4px">{html_escape(concession)}</div>'
    ) if concession else ""

    # Contact footer items
    def _contact_col(icon_d: str, label: str, value: str) -> str:
        return (
            f'<div style="display:flex;align-items:center;gap:10px">'
            f'<div style="width:{circ_sz}px;height:{circ_sz}px;border-radius:50%;background:{theme["primary"]};'
            f'display:flex;align-items:center;justify-content:center;flex-shrink:0">'
            f'{_svg(icon_d, check_icon, "white")}</div>'
            f'<div>'
            f'<div style="font-size:{f["label"]-2}px;color:{theme["text_muted"]};text-transform:uppercase;letter-spacing:1px">{label}</div>'
            f'<div style="font-size:{f["label"]}px;font-weight:700;color:{theme["text_dark"]}">{value}</div>'
            f'</div></div>'
        )

    # Description text: prefer subheadline over about_text for conciseness
    desc_text = (subheadline or about_text)[:220]

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>Poster</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#FFFFFF}}
.poster{{width:{d['width']}px;height:{d['height']}px;display:flex;flex-direction:column;overflow:hidden;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif}}
</style></head><body>
<div class="poster">

  <!-- ── BLUE TOP SECTION ─────────────────────────────────── -->
  <div style="background:{theme['primary']};padding:{pad}px {pad}px {gap}px;display:flex;flex-direction:column;gap:{gap}px">

    <!-- Property name + huge availability + dot corners -->
    <div style="display:flex;align-items:flex-start;justify-content:space-between">
      <div style="flex-shrink:0;padding-top:4px">{_dots(dot_sz)}</div>
      <div style="text-align:center;flex:1;padding:0 {gap}px">
        <div style="font-size:{name_size}px;font-weight:700;color:white;letter-spacing:3px;
          text-transform:uppercase;line-height:1.3">{property_name}</div>
        <div style="font-size:{avail_size}px;font-weight:900;color:white;letter-spacing:2px;
          text-transform:uppercase;line-height:0.92;font-family:Georgia,serif">{availability.upper()}</div>
      </div>
      <div style="flex-shrink:0;padding-top:4px">{_dots(dot_sz)}</div>
    </div>

    <!-- 3 photos with white borders -->
    <div style="display:flex;gap:{photo_gap}px">
      {photos_html}
    </div>

    <!-- Centered white price card -->
    <div style="background:white;align-self:center;padding:{gap}px {pad + gap}px;text-align:center;
      min-width:40%">
      <div style="font-size:{f['label']}px;font-weight:700;color:{theme['primary']};
        text-transform:uppercase;letter-spacing:2.5px">Monthly Rent</div>
      <div style="font-size:{price_big}px;font-weight:900;color:{theme['primary']};
        font-family:Georgia,serif;line-height:1.05">{pricing}</div>
      {concession_line}
    </div>

  </div>

  <!-- ── WHITE BOTTOM SECTION ─────────────────────────────── -->
  <div style="flex:1;background:white;display:flex;flex-direction:column;align-items:center;
    padding:{gap*2}px {pad}px {gap}px;gap:{gap}px;overflow:hidden">

    <!-- HOME FEATURES pill badge -->
    <div style="background:{theme['primary']};color:white;padding:7px 28px;border-radius:30px;
      font-size:{f['label']}px;font-weight:700;letter-spacing:2px;text-transform:uppercase;
      flex-shrink:0">Home Features</div>

    <!-- 3×2 feature grid -->
    <div style="display:flex;flex-wrap:wrap;gap:{gap//2}px {gap*3}px;justify-content:center;
      width:100%;flex-shrink:0">
      {feat_items}
    </div>

    <!-- Description paragraph -->
    <p style="font-size:{f['body']}px;color:{theme['text_muted']};line-height:1.65;
      text-align:center;max-width:88%;flex-shrink:0">{desc_text}</p>

    <!-- Rounded pill CTA button -->
    <div style="background:{theme['primary']};color:white;padding:11px 44px;border-radius:30px;
      font-size:{f['cta']}px;font-weight:700;letter-spacing:2px;text-transform:uppercase;
      flex-shrink:0">{cta_text}</div>

    <!-- Contact row -->
    <div style="display:flex;justify-content:center;gap:{pad*2}px;margin-top:auto;
      width:100%;flex-shrink:0">
      {_contact_col(_PHONE_D, "Call for more information", phone)}
      {_contact_col(_GLOB_D,  "Visit our website",         website)}
    </div>

  </div>
</div></body></html>"""


# ─── Template dispatch ────────────────────────────────────────────────────────

TEMPLATE_FUNCTIONS = [
    None,
    template_hero_overlay,    # 1: classic — white text-left / image-right
    template_split_panel,     # 2: reversed — image-left / info-right
    template_bold_statement,  # 3: image-top band / two-column content below
    template_framed_card,     # 4: editorial card — premium white layout
    template_gradient_story,  # 5: dark primary panel left / image right
    template_blue_hero,       # 6: blue hero poster — primary-bg headline + photos + white content
]

# ─── Per-lever template map ────────────────────────────────────────────────────
# Each lever maps to 3 TEMPLATE_FUNCTIONS indices, chosen for emotional/visual fit.
# LLM returns template_number 1-3; we look up the actual function index here.
#
#  Layouts:  1=classic(text-left/img-right)  2=split(img-left/text-right)
#            3=bold(img-top/2col)             4=framed-card(editorial)
#            5=dark-panel(primary-left/img-right)  6=blue-hero-poster

LEVER_TEMPLATE_MAP: Dict[str, List[int]] = {
    # T1 = welcoming classic   T2 = editorial card    T3 = blue hero poster
    "move_in_ease":  [1, 4, 6],
    # T1 = image-left urban    T2 = bold img-top      T3 = blue hero poster
    "convenience":   [2, 3, 6],
    # T1 = img-top price-hero  T2 = value classic     T3 = blue hero poster
    "affordability": [3, 1, 6],
    # T1 = framed premium      T2 = noir dark panel   T3 = elegant classic
    "luxury":        [4, 5, 1],
    # T1 = features classic    T2 = social img-left   T3 = blue hero poster
    "community":     [1, 2, 6],
    # T1 = magazine editorial  T2 = sleek dark        T3 = visual img-top
    "lifestyle":     [4, 5, 3],
    # T1 = bold img-top        T2 = dark urgent       T3 = reversed decisive
    "urgency":       [3, 5, 2],
    # T1 = trustworthy classic T2 = editorial safe    T3 = blue hero poster
    "family_safety": [1, 4, 6],
}

# ─── LLM response parser ──────────────────────────────────────────────────────

def _parse_template_choices(llm_response: str, brief_count: int) -> List[int]:
    """Parse LLM JSON; returns list of template numbers 1-3 (one per brief)."""
    defaults = [(i % 3) + 1 for i in range(brief_count)]
    try:
        text = (llm_response or "").strip()
        idx  = text.find("{")
        if idx == -1:
            return defaults
        data, _ = json.JSONDecoder().raw_decode(text, idx)
        selections = data.get("template_selections", [])
        result = [max(1, min(3, int(item.get("template_number", 1)))) for item in selections[:brief_count]]
        while len(result) < brief_count:
            result.append(1)
        return result
    except Exception:
        return defaults


# ─── HTML → PNG ───────────────────────────────────────────────────────────────

async def html_to_png_async(html_content: str, output_path: str, width: int, height: int) -> bool:
    try:
        from playwright.async_api import async_playwright
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as tmp:
            tmp.write(html_content)
            temp_html = tmp.name
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page    = await browser.new_page(viewport={"width": width, "height": height})
            await page.goto(f"file://{temp_html}")
            await page.screenshot(path=output_path)
            await browser.close()
        try:
            os.remove(temp_html)
        except OSError:
            pass
        logger.info(f"  ✓ PNG: {Path(output_path).name}")
        return True
    except ImportError:
        logger.warning("Playwright not available — HTML-only mode")
        return False
    except Exception as e:
        logger.error(f"PNG conversion failed: {e}")
        return False


# ─── Main agent ───────────────────────────────────────────────────────────────

@pre_compose()
async def visual_creator(llm_response, input_data, context):
    """
    Visual Creator Agent — professional flat-design real estate poster generator.
    Matches industry-standard listing flyer layout (reference: Century 21 / realty-cards style):
    - Text NEVER overlaid on images — all text in white/beige panels
    - Two-column hero: text panel / clean property image
    - HOME FEATURES beige box with bullet list
    - Dark primary block: START PRICE (large serif) + Discount badge when concession present
    - 3-photo gallery row with room labels
    - ABOUT THIS PROPERTY beige section
    - Footer: circular brand logo + QR code + contact columns
    Platform formats: Instagram Square 1080×1080, Instagram Portrait 1080×1350, Facebook Post 1200×630.
    """
    logger.info("🎨 Visual Creator starting...")

    campaign_briefs = _parse_input(input_data.get("campaign_briefs", "[]"), [])
    if isinstance(campaign_briefs, dict):
        campaign_briefs = campaign_briefs.get("campaign_briefs", [])

    property_photos  = _parse_input(input_data.get("property_photos", "[]"), [])
    amenity_list     = _parse_input(input_data.get("amenity_list", "[]"), [])
    sq_footage_map   = input_data.get("sq_footage_map", "{}")

    contact_phone    = input_data.get("contact_phone", "(512) 555-0100")
    contact_website  = input_data.get("contact_website", "www.leasingoffice.com")
    contact_address  = input_data.get("contact_address", "")
    property_name    = input_data.get("property_name", "Luxury Apartments")
    availability     = input_data.get("availability", "For Rent")

    briefs_to_process = campaign_briefs[:3]
    template_choices  = _parse_template_choices(llm_response, len(briefs_to_process))
    logger.info(f"Briefs: {len(briefs_to_process)} | Templates: {template_choices}")

    output_dir = Path("/Users/bhumkamehndiratta/Desktop/Leafcraft/NewSocialMedia/SocialMediaMarketing_v2/generated_posters")
    output_dir.mkdir(exist_ok=True)

    poster_designs:    List[Dict] = []
    poster_files_saved: int       = 0
    ratio_types = ["instagram_square", "instagram_portrait", "facebook_post"]

    for i, brief in enumerate(briefs_to_process, 1):
        lever     = brief.get("emotional_lever", "convenience")
        persona   = brief.get("renter_persona", "general")
        floorplan = brief.get("target_floorplan", "apartment")

        theme        = LEVER_THEMES.get(lever, LEVER_THEMES[_FALLBACK_LEVER])
        template_num = template_choices[i - 1]

        brief_headlines = brief.get("headlines", [])
        headline = brief_headlines[0] if brief_headlines else theme["headline"]

        ksp         = brief.get("key_selling_points", [])
        subheadline = brief.get("messaging_direction") or (ksp[0] if ksp else "") or "Discover apartment living reimagined."
        description = " • ".join(str(p) for p in ksp[:3]) if ksp else ""

        about_text = brief.get("messaging_direction") or description or (
            f"Premium {floorplan} residences thoughtfully designed for {persona.replace('_', ' ')} living. "
            "Modern finishes, exceptional amenities, and a location that works for your lifestyle."
        )

        hero_idx        = (i - 1) % max(len(property_photos), 1)
        image_url       = property_photos[hero_idx].get("url", FALLBACK_IMAGE) if property_photos else FALLBACK_IMAGE
        beds_baths      = _extract_beds_baths(floorplan)
        sqft            = _extract_sqft(sq_footage_map, floorplan)
        checklist_items = ksp[:6] if ksp else amenity_list[:6]
        concession_flag = brief.get("concession_flag", False)
        concession_det  = brief.get("concession_details", "") if concession_flag else ""

        lever_templates    = LEVER_TEMPLATE_MAP.get(lever, LEVER_TEMPLATE_MAP[_FALLBACK_LEVER])
        actual_template_idx = lever_templates[template_num - 1]
        template_fn         = TEMPLATE_FUNCTIONS[actual_template_idx]

        poster_spec: Dict[str, Any] = {
            "poster_id":           f"poster_{i:03d}",
            "brief_id":            brief.get("brief_id", f"brief_{i:03d}"),
            "name":                f"{persona.replace('_', ' ').title()} — {floorplan}",
            "target_persona":      persona,
            "target_floorplan":    floorplan,
            "emotional_lever":     lever,
            "template_used":       template_num,
            "template_function":   actual_template_idx,
            "property_name":       property_name,
            "availability_status": brief.get("availability_status", availability),
            "headline":            headline,
            "subheadline":         str(subheadline)[:120],
            "description_text":    description,
            "about_text":          about_text,
            "call_to_action":      theme["cta"],
            "pricing_info":        _extract_price(input_data.get("current_pricing", {}), floorplan),
            "bedrooms":            beds_baths["beds"],
            "bathrooms":           beds_baths["baths"],
            "sq_footage":          sqft,
            "room_photos":         _build_room_photos(property_photos, hero_idx),
            "amenities":           checklist_items,
            "concession_flag":     concession_flag,
            "concession_details":  concession_det,
            "contact_phone":       contact_phone,
            "contact_website":     contact_website,
            "contact_address":     contact_address,
            "photo_selected":      image_url,
            "ratios_generated":    ratio_types,
            "files_created":       [],
        }

        lever_slug = lever[:8]  # keep filenames short
        render_jobs = []
        for ratio_type in ratio_types:
            html_content = template_fn(poster_spec, ratio_type, image_url, theme)
            html_path    = output_dir / f"poster_{i:03d}_{ratio_type}_{lever_slug}_t{template_num}.html"
            html_path.write_text(html_content, encoding="utf-8")
            poster_spec["files_created"].append(str(html_path))
            png_path = output_dir / f"poster_{i:03d}_{ratio_type}_{lever_slug}_t{template_num}.png"
            dims     = DIMENSIONS[ratio_type]
            render_jobs.append((html_content, str(png_path), dims["width"], dims["height"]))

        png_results = await asyncio.gather(*[
            html_to_png_async(html, path, w, h) for html, path, w, h in render_jobs
        ])
        for (_, png_path, _, _), success in zip(render_jobs, png_results):
            if success:
                poster_spec["files_created"].append(png_path)
                poster_files_saved += 1

        poster_designs.append(poster_spec)
        concession_note = f" | {concession_det[:30]}" if concession_det else ""
        layout_names = ["classic", "img-left", "img-top", "editorial", "dark-panel", "blue-hero"]
        layout_label = layout_names[actual_template_idx - 1] if actual_template_idx <= 6 else str(actual_template_idx)
        logger.info(f"  ✓ Brief {i} → {lever} T{template_num} ({layout_label}) | {beds_baths['beds']} {beds_baths['baths']}{' '+sqft if sqft else ''}{concession_note}")

    logger.info(f"✨ Done: {len(poster_designs)} sets × {len(ratio_types)} = {poster_files_saved} PNGs")
    logger.info(f"📁 {output_dir}")

    return {
        "visual_packages":    json.dumps(poster_designs),
        "briefs_covered":     len(poster_designs),
        "formats_produced":   json.dumps(ratio_types),
        "poster_files_saved": poster_files_saved,
    }
