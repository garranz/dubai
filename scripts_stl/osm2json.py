import json
from typing import get_overloads
from pyproj import Transformer

import json

def get_utm_zone_from_geojson(geojson_path):
    with open(geojson_path) as f:
        data = json.load(f)
    
    # Collect all longitudes from the first feature (or sample more if needed)
    lons = []
    for feature in data['features'][:10]:  # Sample first 10 features
        geom = feature['geometry']
        if geom['type'] == 'Polygon':
            for coord in geom['coordinates'][0]:
                lons.append(coord[0])
        elif geom['type'] == 'MultiPolygon':
            for polygon in geom['coordinates']:
                for coord in polygon[0]:
                    lons.append(coord[0])
    
    # Calculate UTM zone from average longitude
    avg_lon = sum(lons) / len(lons)
    utm_zone = int((avg_lon + 180) / 6) + 1
    
    # Determine hemisphere from latitude (assuming first coord)
    first_lat = data['features'][0]['geometry']['coordinates'][0][0][1]
    hemisphere = 'N' if first_lat >= 0 else 'S'
    
    # EPSG code: 326XX for north, 327XX for south
    epsg_code = f"EPSG:{32600 + utm_zone}" if hemisphere == 'N' else f"EPSG:{32700 + utm_zone}"
    
    return utm_zone, hemisphere, epsg_code, avg_lon

def load_geojson(filename):
    """Load GeoJSON file"""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_nodes_and_buildings_from_geojson(geojson_data, transformer):
    """
    Convert GeoJSON features to OSM-like format with nodes and buildings
    """
    nodes = []
    buildings = []
    node_id = 1
    node_map = {}  # To avoid duplicate nodes
    
    features = geojson_data.get('features', [])
    
    for feature_idx, feature in enumerate(features):
        if feature['type'] != 'Feature':
            continue
            
        geometry = feature.get('geometry', {})
        properties = feature.get('properties', {})
        
        if geometry['type'] == 'Polygon':
            # Process polygon coordinates
            coordinates = geometry['coordinates'][0]  # Get outer ring
            
            building_nodes = []
            
            for coord in coordinates:
                lon, lat = coord[0], coord[1]
                
                # Create a key for this coordinate to avoid duplicates
                coord_key = f"{lon:.10f},{lat:.10f}"
                
                if coord_key not in node_map:
                    # Convert to meters
                    x, y = transformer.transform(lon, lat)
                    
                    node = {
                        'type': 'node',
                        'id': node_id,
                        'lat': lat,
                        'lon': lon,
                        'x': x,
                        'y': y
                    }
                    nodes.append(node)
                    node_map[coord_key] = node_id
                    node_id += 1
                
                building_nodes.append(node_map[coord_key])
            
            # Create building feature
            building = {
                'id': f'geojson_feature_{feature_idx}',
                'type': 'way',
                'tags': {
                    'building': 'yes',
                    'levels': properties.get('levels', '1'),
                    'height': properties.get('height', '10')
                },
                'nodes': building_nodes
            }
            buildings.append(building)
    
    return nodes, buildings

def save_json(data, filename):
    """Save data to JSON file"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved data to {filename}")


def geojson2json( geojson_file: str)->str:

    # Load GeoJSON
    print(f"Loading {geojson_file}...")
    geojson_data = load_geojson(geojson_file)

    zone, hemi, epsg, lon = get_utm_zone_from_geojson(geojson_file)
    print(f"Average longitude: {lon:.2f}°")
    print(f"UTM Zone: {zone}{hemi}")
    print(f"EPSG Code: {epsg}")

    # Create transformer (same as original script)
    transformer = Transformer.from_crs("EPSG:4326", epsg, always_xy=True)

    # Extract nodes and buildings
    print("Processing features...")
    nodes, buildings = extract_nodes_and_buildings_from_geojson(geojson_data, transformer)

    print(f"Extracted {len(nodes)} nodes and {len(buildings)} buildings")

    # Combine data in the same format as the original script
    combined_data = {
        'nodes': nodes,
        'buildings': buildings
    }

    # Save to JSON
    output_file = geojson_file.rsplit( '.', 1 )[0] # remove extension
    output_file += ".gaf.json"
    save_json(combined_data, output_file)
    print("Done!")

    return output_file

if __name__ == "__main__":

    # Input GeoJSON file
    #geojson_file = './shenzhen.geojson'

    ## Output file
    #output_file = "osm_buildings_full.json"

    geojson_file = 'shenzhen.geojson'
    geojson2json( geojson_file )
