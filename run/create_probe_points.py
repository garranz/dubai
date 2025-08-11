import numpy as np
import matplotlib.pyplot as plt

if __name__ == "__main__":
    # define the box size
    x0, x1 = -400, 3663
    y0, y1 = -400, 3490
    z0, z1 = 0, 648

    Nx, Ny, Nz = 18, 20, 15


    Lx, Ly, Lz = x1-x0, y1-y0, z1-z0

    print( f"Total number of points: {Nx*Ny*Nz}" )

    # Corner points
    xp = np.linspace( x0, x1, Nx+1 )
    yp = np.linspace( y0, y1, Ny+1 )
    zp = np.linspace( z0, z1, Nz+1 )

    # Center points
    xp = .5*( xp[:-1] + xp[1:] )
    yp = .5*( yp[:-1] + yp[1:] )
    zp = .5*( zp[:-1] + zp[1:] )

    # Apply stretching in the z direction
    alpha = 3.
    zp = np.sinh(alpha *  zp / Lz  )/ np.sinh(alpha) * Lz

    X, Y, Z = np.meshgrid(xp, yp, zp, indexing='ij')

    ## Create the 3D plot
    #fig = plt.figure(figsize=(10, 8))
    #ax = fig.add_subplot(111, projection='3d')
    ## Plot the points
    #ax.scatter( X.ravel(), Y.ravel(), Z.ravel(), c='blue', s= 1, marker='.' )
    #ax.set_aspect('equal')

    filename = f'input_points_{Nx}x{Ny}x{Nz}.txt'
    # Write to file
    with open(filename, 'w', encoding="ascii") as f:
        # Write header comment
        f.write(f"# Nx Ny Nz: {Nx} {Ny} {Nz}\n")
        # Write point coordinates
        for x,y,z in zip( X.ravel(), Y.ravel(), Z.ravel() ):
            f.write(f"{x} {y} {z}\n")
