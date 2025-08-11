from common import datapath
from ngpost import *

if __name__ == "__main__":

    pp = Probe( datapath / 'geo2_l4', 'points_device' )

    # sort points by x-coordinate
    coords = np.array( [pp.coords[i+1].reshape( 18, 20, 15 ) for i in range(3) ] )

    # the three first data are: step, time, nbins
    p = pp.readvar( 'P' )[3:]

    ux = pp.readvar( 'U-X' )[3:]
    uy = pp.readvar( 'U-Y' )[3:]
    uz = pp.readvar( 'U-Z' )[3:]

    Nxyz = (18,20,15)

    P  = p .reshape( *Nxyz, -1 )
    Ux = ux.reshape( *Nxyz, -1 )
    Uy = uy.reshape( *Nxyz, -1 )
    Uz = uz.reshape( *Nxyz, -1 )
