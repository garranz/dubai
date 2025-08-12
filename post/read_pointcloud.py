from common import datapath
from ngpost import *
from extractcity import stl_to_2d_view
import matplotlib.pyplot as plt

if __name__ == "__main__":

    basenm = 'geo2_l3'
    Nx, Ny, Nz = 18, 20, 15

    pp = PointCloud( datapath / basenm / 'pcprobes', 'points' )
    x,y,z = pp.getpoints()

    # Unique sorted coordinates along each axis
    x_vals = np.unique(x)
    y_vals = np.unique(y)
    z_vals = np.unique(z)

    assert (len(x_vals) == Nx) and (len(y_vals) == Ny) and (len(z_vals) == Nz)

    # Create lookup dicts: coord -> index
    x_idx = {val: i for i, val in enumerate(x_vals)}
    y_idx = {val: i for i, val in enumerate(y_vals)}
    z_idx = {val: i for i, val in enumerate(z_vals)}

    # Initialize NaN grids
    grid_x, grid_y, grid_z = np.meshgrid( x_vals, y_vals, z_vals, indexing='ij')
    #grid_x = np.full((Nx, Ny, Nz), np.nan)
    #grid_y = np.full((Nx, Ny, Nz), np.nan)
    #grid_z = np.full((Nx, Ny, Nz), np.nan)

    # Create NaN-filled matrix for velocity
    vel_avg = np.full((3, Nx, Ny, Nz), np.nan)
    vel_rms = np.full((3, Nx, Ny, Nz), np.nan)
    p_avg = np.full((Nx, Ny, Nz), np.nan)
    p_rms = np.full((Nx, Ny, Nz), np.nan)

    dat = pp.getdata( pp.getifrl()[-1] )
    # Fill them
    for xv, yv, zv, dd in zip(x, y, z, dat.T):
        i, j, k = x_idx[xv], y_idx[yv], z_idx[zv]
        #grid_x[i, j, k] = xv
        #grid_y[i, j, k] = yv
        #grid_z[i, j, k] = zv

        for r_ in range(3):
            vel_avg[r_,i,j,k] = dd[ pp.vlist.index(f'AVG(U)[{r_}]') ]
            vel_rms[r_,i,j,k] = dd[ pp.vlist.index(f'RMS(U)[{r_}]') ]


    ixplot = range( 2, Nx-2, 3 )
    iyplot = range( 2, Ny-2, 3 )

    cols = plt.get_cmap('viridis')(np.linspace(0,1,nn:=len(ixplot)*len(iyplot)))

    builds = stl_to_2d_view( '../stl2/buildings.stl', view='top' )

    f1,a1 = plt.subplots()
    f2,a2 = plt.subplots( 3, 1, sharex=True, sharey=True )
    f3,a3 = plt.subplots( 3, 1, sharex=True, sharey=True )
    a1.add_collection( builds )
    k = 0
    xx = (x_vals - x_vals[0])/30
    for j in iyplot:
        for i in ixplot:
            a1.plot( x_vals[i], y_vals[j], 'o', c=cols[k], ms=12, mec='k', mew=.5 )
            for vin in range(3):
                a2[vin].plot( vel_avg[vin,i,j,:] + xx[i], z_vals, c=cols[k] )
                a2[vin].axvline( xx[i], ls='--', c='.5', lw=.5 )
                a2[vin].set_title( chr(85+vin) )

                a3[vin].plot( vel_rms[vin,i,j,:]*5 + xx[i], z_vals, c=cols[k] )
                a3[vin].axvline( xx[i], ls='--', c='.5', lw=.5 )
                a3[vin].set_title( f'rms({chr(97+20+vin)})' )
            k += 1 
            
    for aa in (a2,a3):
        for a in aa: 
            a.set_ylim( 0, 600 )
            a.set_ylabel( r'$z$ [m]')

    plt.setp( a2[-1], xticks=xx[ixplot], xticklabels=(f'{x_vals[i]:.0f}' for i in
                                                     ixplot ), xlabel=r'$x$ [m]')
    plt.setp( a3[-1], xticks=xx[ixplot], xticklabels=(f'{x_vals[i]:.0f}' for i in
                                                     ixplot ), xlabel=r'$x$ [m]')

    a1.set_xlabel(r'$x$ [m]')
    a1.set_ylabel(r'$y$ [m]')

    for f in (f1,f2,f3): f1.tight_layout()
