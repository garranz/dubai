import trimesh
import os
import sys

def fullstl( stl_input_name: str, stl_output_name: str):

    verbose = True

    # Load main mesh
    mesh1 = trimesh.load(f'box_{stl_input_name}.stl')
    assert isinstance(mesh1, trimesh.Trimesh)

    print("Mesh1 watertight:", mesh1.is_watertight)

    if not mesh1.is_watertight:
        print("Warning: mesh1 is not watertight. Boolean operations may fail or produce unexpected results.")

    # Load building meshes
    buildings_folder = 'buildings'
    building_meshes = []

    for filename in os.listdir(buildings_folder):
        if filename.endswith('.stl'):
            filepath = os.path.join(buildings_folder, filename)
            mesh = trimesh.load(filepath)
            assert isinstance(mesh, trimesh.Trimesh)
            building_meshes.append(mesh)
            if verbose:            
                print(f"Loaded {filename}, watertight: {mesh.is_watertight}")
    
    print(f"Total loaded building meshes: {len(building_meshes)}")
    
    # Filter watertight building meshes
    watertight_buildings = [mesh for mesh in building_meshes if mesh.is_watertight]
    
    if len(watertight_buildings) == 0:
        print("No watertight building meshes found. Exiting.")
        sys.exit(1)
    
    print(f"Number of watertight building meshes: {len(watertight_buildings)}")
    
    current_mesh = mesh1
    
    for i, building in enumerate(watertight_buildings):
    
        #if i == 10:
        #    break
    
        print(f"Subtracting building {i+1}/{len(watertight_buildings)}")
        print(f"Type current_mesh: {type(current_mesh)}, Type building: {type(building)}")
    
        try:
            # Perform boolean difference with lists of meshes
            new_mesh = trimesh.boolean.difference([current_mesh, building])
            
            if new_mesh is None:
                raise RuntimeError(f"Boolean difference returned None at building {i+1}")
            
            elif new_mesh.is_volume is False:
                raise RuntimeError(f"Boolean difference did not produce a valid volume at building {i+1}")
            
            else:
                current_mesh = new_mesh
    
        except Exception as e:
            print(f"Boolean operation failed at building {i+1}: {e}")
            print(f"Type new_mesh: {type(new_mesh)}") # pyright: ignore
            print(f"Type building: {type(building)}")
            print(f"current mesh is volume: {current_mesh.is_volume}")
            print(f"current building is volume: {building.is_volume}")
            # Optionally: break here if failure should stop processing
            continue
    
    print("Boolean difference completed for all buildings.")
    
    # Export result mesh
    current_mesh.export(nn:=f'{stl_output_name}_flow_volume.stl')
    # Check if the resulting mesh is watertight
    if current_mesh.is_watertight:
        print("Resulting mesh is watertight.")
    else:
        print("Warning: Resulting mesh is not watertight. This may affect downstream applications.")
    # Export the resulting mesh to an STL file
    print(f"Exported resulting mesh to {nn}")
