import json
import os
import numpy as np
import trimesh
import shapely.geometry

import shutil
from pathlib import Path
# ------------------------------------------------------------------------------


def load_osm_json(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

# ------------------------------------------------------------------------------


def build_node_index(nodes):
    """Create a dict: node_id -> node with x,y coordinates."""
    return {node['id']: node for node in nodes}

# ------------------------------------------------------------------------------


def extract_polygon_from_way(node_ids, node_index):
    """Return list of (x,y) tuples for the way's nodes."""
    polygon = []
    for nid in node_ids:
        node = node_index.get(nid)
        if node and 'x' in node and 'y' in node:
            polygon.append((node['x'], node['y']))
    return polygon

# ------------------------------------------------------------------------------


def get_building_height(tags, default_floor_height=3.0, min_height=3.0):
    """Compute building height using tags."""
    if not tags:
        return min_height
    if 'height' in tags:
        try:
            return float(tags['height'])
        except ValueError:
            pass
    if 'building:levels' in tags:
        try:
            return float(tags['building:levels']) * default_floor_height
        except ValueError:
            pass
    return min_height

# ------------------------------------------------------------------------------


def extrude_polygon_to_watertight_mesh(polygon, height=10.0):
    """
    Use trimesh with shapely to extrude a 2D polygon into a watertight 3D mesh volume.
    """
    if len(polygon) < 3:
        return None

    polygon_2d = np.array(polygon)

    # Create shapely polygon, try to fix invalid polygons
    poly_shape = shapely.geometry.Polygon(polygon_2d)
    if not poly_shape.is_valid:
        poly_shape = poly_shape.buffer(0)

    if not poly_shape.is_valid or poly_shape.is_empty:
        print("Invalid polygon, skipping extrusion.")
        return None

    # Create trimesh path from shapely polygon
    path = trimesh.load_path(poly_shape)

    # Extrude to get solid mesh
    solid = path.extrude(height)

    # Repair if needed
    if not solid.is_watertight:
        solid = solid.fill_holes()
    # solid.repair.fix_normals()

    if not solid.is_watertight:
        print("Warning: mesh extrusion resulted in a non-watertight mesh.")

    return solid

# ------------------------------------------------------------------------------


def normalize_mesh(mesh_obj, min_coords=(0, 0, 0)):
    """
    Translate mesh to origin based on min_coords and lift slightly above Z=0.
    """
    translation = -np.array(min_coords)
    mesh_obj.apply_translation(translation)
    return mesh_obj

# ------------------------------------------------------------------------------


def create_box_stl(filename,
                   x_len, y_len, z_len,
                   xy_offset=0.0, z_offset=0.0):
    """
    Create a simple box mesh and save as STL for bounding box visualization.
    x_len, y_len, z_len: dimensions of the box.
    xy_offset: offset in X and Y at the edges --> padding.
    z_offset: offset in Z above highest building.
    """
    box = trimesh.creation.box(extents=[x_len+2*xy_offset, y_len+2*xy_offset,
                                        z_len+z_offset])
    box.apply_translation([x_len/2.0,
                           y_len/2.0,
                           z_len/2.0+z_offset/2.0])  # Lift the box above Z=0
    box.export(filename)
    print(f"Box STL saved as '{filename}'.")


def create_box_stl_xoff(filename,
                        x_len, y_len, z_len,
                        x0_offset=0.0, x1_offset=0.0,
                        y_offset=0.0,
                        z_offset=0.0):
    """
    Create a simple box mesh and save as STL for bounding box visualization.

    Parameters:
    -----------
    x_len, y_len, z_len : float
        Base dimensions of the box (before padding).
    x0_offset : float
        Padding on the negative X side (left).
    x1_offset : float
        Padding on the positive X side (right).
    y_offset : float
        Symmetric padding in Y direction (both sides).
    z_offset : float
        Offset in Z above highest building.
    """
    # Calculate total dimensions with asymmetric padding
    total_x = x_len + x0_offset + x1_offset
    total_y = y_len + 2*y_offset
    total_z = z_len + z_offset

    # Create box with total dimensions
    box = trimesh.creation.box(extents=[total_x, total_y, total_z])

    # Calculate translation considering asymmetric x padding
    x_center = x_len/2.0 + (x1_offset - x0_offset)/2.0
    y_center = y_len/2.0
    z_center = z_len/2.0 + z_offset/2.0

    box.apply_translation([x_center, y_center, z_center])
    box.export(filename)
    print(f"Box STL saved as '{filename}'.")


def json2stls( input_json: str, output_stl_name: str,
              x_offsets: tuple[int,int], y_offset: int, z_offset: int):


    output_stl = output_stl_name + '.stl'

    data = load_osm_json(input_json)
    nodes = data.get('nodes', [])
    buildings = data.get('buildings', [])

    node_index = build_node_index(nodes)
    all_meshes = []

    print("Processing buildings to create watertight meshes...")

    for bld in buildings:
        tags = bld.get('tags', {})
        height = get_building_height(tags)

        mesh_obj = None
        if bld['type'] == 'way' and 'nodes' in bld:
            polygon = extract_polygon_from_way(bld['nodes'], node_index)
            if len(polygon) < 3:
                continue
            mesh_obj = extrude_polygon_to_watertight_mesh(
                polygon, height=height)

        elif bld['type'] == 'relation' and 'members' in bld:
            # Skip complex multipolygon relations for now
            continue

        if mesh_obj:
            all_meshes.append(mesh_obj)

    assert all_meshes, "No building geometry found to write."

    combined = trimesh.util.concatenate(all_meshes)
    bbox_min, bbox_max = combined.bounds

    # Normalize combined mesh to origin
    combined = normalize_mesh(combined, min_coords=bbox_min)
    combined.export(output_stl)
    print(f"Saved combined watertight STL file as {output_stl}")

    bbox_size = bbox_max - bbox_min
    print(f"Bounding box min: {bbox_min}, max: {bbox_max}")
    print(f"Bounding box size (dx, dy, dz): {bbox_size}")

    # Create box STL for bounding box visualization
    create_box_stl_xoff(f"box_{output_stl_name}.stl",
                        *bbox_size,
                        x0_offset=x_offsets[0], x1_offset=x_offsets[1],
                        y_offset=y_offset,
                        z_offset=z_offset)  # bbox_size[2]/2.0)

    # ===== Export individual building meshes =====
    path = Path("buildings")
    if path.exists():
        shutil.rmtree(path)
    os.makedirs("buildings", exist_ok=True)
    building_counter = 1

    for bld in buildings:
        tags = bld.get('tags', {})
        height = get_building_height(tags)

        mesh_obj = None
        if bld['type'] == 'way' and 'nodes' in bld:
            polygon = extract_polygon_from_way(bld['nodes'], node_index)
            if len(polygon) < 3:
                continue
            mesh_obj = extrude_polygon_to_watertight_mesh(
                polygon, height=height)

        elif bld['type'] == 'relation' and 'members' in bld:
            continue  # skip relations here as well

        if mesh_obj:
            mesh_obj = normalize_mesh(mesh_obj, min_coords=bbox_min)
            filename = f"building_{building_counter:07d}.stl"
            filepath = os.path.join("buildings", filename)
            mesh_obj.export(filepath)
            print(f"Saved individual building STL: {filename}")
            building_counter += 1

    if building_counter == 1:
        print("No individual building meshes were created.")
    else:
        print(
            f"Saved {building_counter - 1} individual watertight building STL files.")

    print("Done.")


