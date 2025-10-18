import pyvista as pv
import numpy as np
from common import datapath


import pyvista as pv
from stl import mesh
import numpy as np
from scipy.interpolate import griddata

import numpy as np
from stl import mesh
from scipy.spatial import Delaunay
import matplotlib.pyplot as plt
from matplotlib.path import Path

def point_in_triangle_2d(p, tri):
    """Check if point p is inside triangle tri using barycentric coordinates."""
    v0 = tri[2] - tri[0]
    v1 = tri[1] - tri[0]
    v2 = p - tri[0]
    
    dot00 = np.dot(v0, v0)
    dot01 = np.dot(v0, v1)
    dot02 = np.dot(v0, v2)
    dot11 = np.dot(v1, v1)
    dot12 = np.dot(v1, v2)
    
    inv_denom = 1 / (dot00 * dot11 - dot01 * dot01)
    u = (dot11 * dot02 - dot01 * dot12) * inv_denom
    v = (dot00 * dot12 - dot01 * dot02) * inv_denom
    
    return (u >= 0) and (v >= 0) and (u + v <= 1)


def rasterize_triangle_2d(tri_xy, tri_z, x_grid, y_grid, height_map):
    """
    Rasterize a 3D triangle onto a 2D height map.
    Updates height_map in place with maximum z values.
    
    Parameters:
    -----------
    tri_xy : array (3, 2)
        Triangle vertices in x-y coordinates
    tri_z : array (3,)
        z-coordinates of triangle vertices
    x_grid : array (nx,)
        x coordinates of grid
    y_grid : array (ny,)
        y coordinates of grid
    height_map : array (nx, ny)
        Height map to update
    """
    # Get bounding box of triangle
    x_min, x_max = tri_xy[:, 0].min(), tri_xy[:, 0].max()
    y_min, y_max = tri_xy[:, 1].min(), tri_xy[:, 1].max()
    
    # Find grid indices for bounding box
    i_min = max(0, np.searchsorted(x_grid, x_min) - 1)
    i_max = min(len(x_grid), np.searchsorted(x_grid, x_max) + 1)
    j_min = max(0, np.searchsorted(y_grid, y_min) - 1)
    j_max = min(len(y_grid), np.searchsorted(y_grid, y_max) + 1)
    
    # Create Path object for the triangle
    triangle_path = Path(tri_xy)
    
    # Check all grid points in bounding box
    for i in range(i_min, i_max):
        for j in range(j_min, j_max):
            point = np.array([x_grid[i], y_grid[j]])
            
            # Check if point is inside triangle
            if triangle_path.contains_point(point):
                # Interpolate z value using barycentric coordinates
                v0 = tri_xy[2] - tri_xy[0]
                v1 = tri_xy[1] - tri_xy[0]
                v2 = point - tri_xy[0]
                
                dot00 = np.dot(v0, v0)
                dot01 = np.dot(v0, v1)
                dot02 = np.dot(v0, v2)
                dot11 = np.dot(v1, v1)
                dot12 = np.dot(v1, v2)
                
                denom = dot00 * dot11 - dot01 * dot01
                if abs(denom) > 1e-10:
                    inv_denom = 1 / denom
                    u = (dot11 * dot02 - dot01 * dot12) * inv_denom
                    v = (dot00 * dot12 - dot01 * dot02) * inv_denom
                    
                    # Interpolate z value
                    z_interp = tri_z[0] + u * (tri_z[2] - tri_z[0]) + v * (tri_z[1] - tri_z[0])
                    
                    # Update height map with maximum z value
                    height_map[i, j] = max(height_map[i, j], z_interp)


def stl_to_heightmap(
    stl_file_path,
    bounds=None,
    resolution=(500, 500),
    ground_level=None
):
    """
    Create a 2D height map from an STL file of city buildings.
    Fills in the area enclosed by each building.
    
    Parameters:
    -----------
    stl_file_path : str
        Path to the STL file
    bounds : tuple or None
        Bounds for the 2D grid as (xmin, xmax, ymin, ymax).
        If None, uses the bounds from the STL.
    resolution : tuple
        Number of points in x and y directions (nx, ny)
    ground_level : float or None
        If provided, sets the initial ground level
        
    Returns:
    --------
    dict containing:
        'x': 1D numpy array of x coordinates
        'y': 1D numpy array of y coordinates
        'height': 2D numpy array of heights, shape (nx, ny)
        'bounds': (xmin, xmax, ymin, ymax, zmin, zmax)
    """
    
    # Read the STL file
    print(f"Reading STL file from {stl_file_path}...")
    city_mesh = mesh.Mesh.from_file(stl_file_path)
    
    # Get all vertices
    print(f"\nMesh info:")
    print(f"  Number of triangles: {len(city_mesh.vectors)}")
    
    # Extract bounds
    all_points = city_mesh.vectors.reshape(-1, 3)
    x_coords = all_points[:, 0]
    y_coords = all_points[:, 1]
    z_coords = all_points[:, 2]
    
    # Set bounds for the 2D grid
    if bounds is None:
        xmin, xmax = x_coords.min(), x_coords.max()
        ymin, ymax = y_coords.min(), y_coords.max()
    else:
        xmin, xmax, ymin, ymax = bounds
    
    zmin, zmax = z_coords.min(), z_coords.max()
    
    print(f"\nSTL bounds:")
    print(f"  X range: [{xmin:.2f}, {xmax:.2f}]")
    print(f"  Y range: [{ymin:.2f}, {ymax:.2f}]")
    print(f"  Z range: [{zmin:.2f}, {zmax:.2f}]")
    print(f"  Resolution: {resolution}")
    
    # Create uniform grid
    nx, ny = resolution
    x = np.linspace(xmin, xmax, nx)
    y = np.linspace(ymin, ymax, ny)
    
    # Initialize height map
    if ground_level is None:
        ground_level = zmin
    height_map = np.full((nx, ny), ground_level)
    
    print(f"\nRasterizing {len(city_mesh.vectors)} triangles...")
    
    # Process each triangle
    for idx, triangle in enumerate(city_mesh.vectors):
        if idx % 10000 == 0 and idx > 0:
            print(f"  Processed {idx}/{len(city_mesh.vectors)} triangles...")
        
        # Extract x, y, z coordinates
        tri_xy = triangle[:, :2]  # shape (3, 2)
        tri_z = triangle[:, 2]     # shape (3,)
        
        # Rasterize this triangle
        rasterize_triangle_2d(tri_xy, tri_z, x, y, height_map)
    
    print(f"Rasterization complete!")
    
    print(f"\nHeight map statistics:")
    print(f"  Min height: {height_map.min():.2f}")
    print(f"  Max height: {height_map.max():.2f}")
    print(f"  Mean height: {height_map.mean():.2f}")
    
    result = {
        'x': x,
        'y': y,
        'height': height_map,
        'bounds': (xmin, xmax, ymin, ymax, zmin, zmax)
    }
    
    return result


def save_heightmap(result, filename):
    """Save heightmap to numpy file."""
    np.savez(filename, 
             x=result['x'], 
             y=result['y'], 
             height=result['height'],
             bounds=result['bounds'])
    print(f"Saved heightmap to {filename}")


def plot_heightmap(result, figsize=(12, 10), save_path=None):
    """
    Visualize the height map.
    
    Parameters:
    -----------
    result : dict
        Output from stl_to_heightmap
    figsize : tuple
        Figure size
    save_path : str or None
        If provided, saves figure to this path
    """
    from matplotlib.colors import LightSource
    
    x, y, height = result['x'], result['y'], result['height']
    
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    
    # Plot 1: Simple height map
    im1 = axes[0].imshow(height.T, origin='lower', 
                         extent=[x.min(), x.max(), y.min(), y.max()],
                         cmap='terrain', aspect='auto')
    axes[0].set_xlabel('X coordinate (m)')
    axes[0].set_ylabel('Y coordinate (m)')
    axes[0].set_title('City Height Map')
    plt.colorbar(im1, ax=axes[0], label='Height (m)')
    
    # Plot 2: Hillshade effect
    ls = LightSource(azdeg=315, altdeg=45)
    hillshade = ls.hillshade(height.T, vert_exag=2, dx=1, dy=1)
    axes[1].imshow(hillshade, origin='lower',
                   extent=[x.min(), x.max(), y.min(), y.max()],
                   cmap='gray', aspect='auto')
    axes[1].set_xlabel('X coordinate (m)')
    axes[1].set_ylabel('Y coordinate (m)')
    axes[1].set_title('Hillshade View')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved figure to {save_path}")
    
    plt.show()
    
    return fig




def interpolate_unstructured_to_uniform(
    vtk_file_path,
    bounds=None,
    dimensions=(50, 50, 50),
    output_file=None,
    return_numpy=True
):
    """
    Read an unstructured grid VTK file and interpolate onto a uniform grid.
    
    Parameters:
    -----------
    vtk_file_path : str
        Path to the input VTK file
    bounds : tuple or None
        Bounds for the uniform grid as (xmin, xmax, ymin, ymax, zmin, zmax).
        If None, uses the bounds of the unstructured grid.
    dimensions : tuple
        Number of points in each direction (nx, ny, nz) for the uniform grid
    output_file : str or None
        If provided, saves the interpolated grid to this file
    return_numpy : bool
        If True, returns numpy arrays. If False, returns PyVista grid object.
        
    Returns:
    --------
    If return_numpy=True:
        dict containing:
            'coordinates': dict with 'x', 'y', 'z' as 1D numpy arrays
            'grid_shape': tuple (nx, ny, nz)
            'variables': dict with variable_name -> numpy array (shape: nx, ny, nz)
    If return_numpy=False:
        uniform_grid : pyvista.ImageData
    """
    
    # Read the unstructured grid
    print(f"Reading unstructured grid from {vtk_file_path}...")
    unstructured_grid = pv.read(vtk_file_path)
    
    # Print information about the data
    print(f"\nUnstructured grid info:")
    print(f"  Number of points: {unstructured_grid.n_points}")
    print(f"  Number of cells: {unstructured_grid.n_cells}")
    print(f"  Bounds: {unstructured_grid.bounds}")
    print(f"  Point data arrays: {unstructured_grid.point_data.keys()}")
    print(f"  Cell data arrays: {unstructured_grid.cell_data.keys()}")
    
    # Set bounds for uniform grid
    if bounds is None:
        bounds = unstructured_grid.bounds
    
    print(f"\nCreating uniform grid with:")
    print(f"  Bounds: {bounds}")
    print(f"  Dimensions: {dimensions}")
    
    # Create uniform grid
    uniform_grid = pv.ImageData()
    uniform_grid.dimensions = dimensions
    uniform_grid.origin = (bounds[0], bounds[2], bounds[4])
    uniform_grid.spacing = (
        (bounds[1] - bounds[0]) / (dimensions[0] - 1),
        (bounds[3] - bounds[2]) / (dimensions[1] - 1),
        (bounds[5] - bounds[4]) / (dimensions[2] - 1)
    )
    
    # Interpolate data from unstructured to uniform grid
    print("\nInterpolating data...")
    uniform_grid = uniform_grid.sample(unstructured_grid)
    
    print(f"\nInterpolated grid info:")
    print(f"  Number of points: {uniform_grid.n_points}")
    print(f"  Point data arrays: {uniform_grid.point_data.keys()}")
    
    # Save if output file specified
    if output_file:
        print(f"\nSaving to {output_file}...")
        uniform_grid.save(output_file)
    
    # Return numpy arrays if requested
    if return_numpy:
        nx, ny, nz = dimensions
        
        # Get coordinate arrays
        x = np.linspace(bounds[0], bounds[1], nx)
        y = np.linspace(bounds[2], bounds[3], ny)
        z = np.linspace(bounds[4], bounds[5], nz)
        
        # Get all interpolated variables as numpy arrays
        variables = {}
        for array_name in uniform_grid.point_data.keys():
            # Get the data and reshape to 3D grid
            data = uniform_grid.point_data[array_name]
            
            # Handle scalar and vector data
            if data.ndim == 1:
                # Scalar data
                variables[array_name] = data.reshape((nx, ny, nz), order='F')
            else:
                # Vector data (e.g., velocity with 3 components)
                # Shape will be (nx, ny, nz, n_components)
                n_components = data.shape[1]
                variables[array_name] = data.reshape((nx, ny, nz, n_components), order='F')
            
            print(f"Variable '{array_name}': shape = {variables[array_name].shape}")
        
        result = {
            'coordinates': {'x': x, 'y': y, 'z': z},
            'grid_shape': (nx, ny, nz),
            'variables': variables
        }
        
        return result
    else:
        return uniform_grid


# Example usage
if __name__ == "__main__":
    basenm = 'geo3_l6'
    fnm = datapath / basenm / 'data' / \
            f'{basenm}_vtu_volume_avg.32000000.vtu'

    Nx, Ny, Nz = 288, 288, 88
    Dd = 4
    x0, y0 = 500, 500


    # Usage with custom subset bounds
    # (xmin, xmax, ymin, ymax, zmin, zmax)
    custom_bounds = (x0, x0+Dd*Nx, y0, y0+Dd*Ny, 0.0, Dd*Nz)  

    '''

    # Get data as numpy arrays
    result = interpolate_unstructured_to_uniform(
        vtk_file_path=fnm,
        bounds=custom_bounds,
        dimensions=(Nx,Ny,Nz),
        return_numpy=True
    )

    # Access coordinates
    x = result['coordinates']['x']
    y = result['coordinates']['y']
    z = result['coordinates']['z']
    nx, ny, nz = result['grid_shape']

    print(f"\nCoordinate arrays:")
    print(f"  x: shape {x.shape}, range [{x.min():.3f}, {x.max():.3f}]")
    print(f"  y: shape {y.shape}, range [{y.min():.3f}, {y.max():.3f}]")
    print(f"  z: shape {z.shape}, range [{z.min():.3f}, {z.max():.3f}]")
    '''


    # Create height map from STL
    result = stl_to_heightmap(
        stl_file_path="../stl/buildings.stl",
        bounds = custom_bounds[:-2],
        resolution=(Nx,Ny),  # 500x500 grid
        ground_level=0.0  # Set ground to z=0
    )

    ''' 
    # Access the data
    x = result['x']  # 1D array, shape (500,)
    y = result['y']  # 1D array, shape (500,)
    height = result['height']  # 2D array, shape (500, 500)
    
    print(f"\nOutput arrays:")
    print(f"  x: shape {x.shape}")
    print(f"  y: shape {y.shape}")
    print(f"  height: shape {height.shape}")
    
    # Save to file
    save_heightmap(result, 'city_heightmap.npz')
    
    # Visualize
    plot_heightmap(result, save_path='city_heightmap.png')

    '''

    dat = np.load( 'x0_500_y0_500_var.npz')
    U = np.transpose( dat['AVG(U)'], (3, 0, 1, 2) ).astype(np.float32)
    H = result['height'].astype(np.float32)

    f1,a1 = plt.subplots(1,4, figsize=(12,3), constrained_layout=True)
    a1[0].pcolormesh( H.T )
    for i in range(3): a1[1+i].pcolormesh( U[i,...,20].T,
                                          cmap=plt.get_cmap('RdBu'),)


    np.savez( 'validation_Dubai_test', U = U, z = H )
