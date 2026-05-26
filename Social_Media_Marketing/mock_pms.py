#!/usr/bin/env python3
"""
Mock PMS (Property Management System) server for testing
Responds to data_ingest requests with test data
"""
import json
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Test data that matches PMS API response format
PMS_TEST_DATA = {
    "floorplans": {
        "studio": {
            "total_units": 40,
            "occupied_units": 35,
            "pricing": 1200
        },
        "one_bedroom": {
            "total_units": 80,
            "occupied_units": 72,
            "pricing": 1650
        },
        "two_bedroom": {
            "total_units": 100,
            "occupied_units": 88,
            "pricing": 2100
        },
        "three_bedroom": {
            "total_units": 30,
            "occupied_units": 27,
            "pricing": 2800
        }
    },
    "photos": [
        {"url": "photo1.jpg", "caption": "Luxury lobby", "tags": ["lobby", "modern"]},
        {"url": "photo2.jpg", "caption": "2BR floor plan", "tags": ["bedroom", "floorplan"]},
        {"url": "photo3.jpg", "caption": "Gym facility", "tags": ["amenity", "fitness"]},
        {"url": "photo4.jpg", "caption": "Pool area", "tags": ["amenity", "outdoor"]},
        {"url": "photo5.jpg", "caption": "Community room", "tags": ["amenity", "social"]},
    ],
    "concessions": [
        {"type": "waived_deposit", "floorplans": ["two_bedroom"], "value": 500},
        {"type": "move_in_credit", "floorplans": ["studio", "one_bedroom"], "value": 100}
    ],
    "address": "1450 Riverside Drive, Denver, CO 80210",
    "coordinates": "39.7392,-104.9903",
    "amenities": [
        "Swimming pool",
        "Fitness center", 
        "Dog park",
        "Community room",
        "Rooftop lounge",
        "Concierge",
        "24-hour security",
        "Reserved parking",
        "Package room",
        "Bike storage"
    ]
}

class PMSHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        
        # Mock /api/v1/listings endpoint
        if path == "/api/v1/listings":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(PMS_TEST_DATA).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress logging
        pass

def run_mock_pms(port=8765):
    server = HTTPServer(("127.0.0.1", port), PMSHandler)
    print(f"🏢 Mock PMS Server running on http://127.0.0.1:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run_mock_pms()
