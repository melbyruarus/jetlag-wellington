import requests
import json
import sys
import argparse

def get_osm_data(key_filter, value_filter):
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    # Overpass Query using exact regex matching
    overpass_query = f"""
    [out:json][timeout:30];
    area["name"="Wellington City"]->.searchArea;
    (
      nwr[~"^{key_filter}$"~"^{value_filter}$"]["name"](area.searchArea);
    );
    out center;
    """

    try:
        # Status update to stderr
        print(f"Querying Overpass for {key_filter}={value_filter} in Wellington...", file=sys.stderr)
        
        response = requests.get(overpass_url, params={'data': overpass_query})
        response.raise_for_status()
        data = response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Network/API Error: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: Received invalid JSON from Overpass API.", file=sys.stderr)
        sys.exit(1)

    # Initialize GeoJSON structure
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }

    # Process elements
    for element in data.get('elements', []):
        if element['type'] == 'node':
            lon, lat = element['lon'], element['lat']
        elif 'center' in element:
            lon, lat = element['center']['lon'], element['center']['lat']
        else:
            continue

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            },
            "properties": {
                "name": element.get('tags', {}).get('name', 'Unnamed')
            }
        }
        geojson["features"].append(feature)

    # Report result count to stderr
    count = len(geojson["features"])
    print(f"Success: Found {count} results.", file=sys.stderr)

    # Output pure JSON to stdout
    json.dump(geojson, sys.stdout, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query Wellington OSM data and output clean GeoJSON.")
    parser.add_argument("key", help='OSM key (e.g., "amenity" or "leisure")')
    parser.add_argument("value", help='OSM value or regex (e.g., "cinema" or "park|garden")')
    
    args = parser.parse_args()
    get_osm_data(args.key, args.value)