import collections
import numpy as np
import matplotlib.pyplot as plt
from stl import mesh
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
import trimesh

def stl_to_2d_view(stl_path, view='top'):
    """
    Convert STL file to 2D view and plot it.

    Parameters:
    -----------
    stl_path : str
        Path to the STL file
    view : str
        View perspective ('top', 'front', 'side')
    """

    # Load the STL file
    city_mesh = mesh.Mesh.from_file(stl_path)

    # Extract vertices
    vertices = city_mesh.vectors.reshape(-1, 3)

    # Choose projection based on view
    if view == 'top':
        # Project onto XY plane (ignore Z)
        x = vertices[:, 0]
        y = vertices[:, 1]
    elif view == 'front':
        # Project onto XZ plane (ignore Y)
        x = vertices[:, 0]
        y = vertices[:, 2]
    elif view == 'side':
        # Project onto YZ plane (ignore X)
        x = vertices[:, 1]
        y = vertices[:, 2]
    else:
        raise ValueError

    # Plot filled triangles
    patches = []
    for i in range(0, len(vertices), 3):
        triangle = Polygon([(x[i], y[i]), 
                           (x[i+1], y[i+1]), 
                           (x[i+2], y[i+2])])
        patches.append(triangle)

    return PatchCollection(patches, facecolor='lightgray', 
                                edgecolor='black', 
                                linewidth=0.3)




# Example usage
if __name__ == "__main__":
    # Replace with your STL file path
    stl_file = "./buildings.stl"
    # Top view with filled polygons
    # Create figure

    collection = stl_to_2d_view(stl_file, view='top' )

    fig, ax = plt.subplots()#figsize=(12, 10))
    ax.add_collection(collection)

