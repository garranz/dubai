from common import datapath
from ngpost import *

if __name__ == "__main__":

    pp = Probe( datapath / 'geo2_l4', 'points' )

    # sort points by x-coordinate
    coords = np.array( [pp.coords[i+1].reshape( 18, 20, 15 ) for i in range(3) ] )

    # the three first data are: step, time, nbins
    pave = pp.readvar( 'AVG(P)' )[3:]
    prsm = pp.readvar( 'RMS(P)' )[3:]

    uxave = pp.readvar( 'AVG(U)-X' )[3:]
    uxrms = pp.readvar( 'RMS(U)-X' )[3:]
    uyave = pp.readvar( 'AVG(U)-Y' )[3:]
    uyrms = pp.readvar( 'RMS(U)-Y' )[3:]
    uzave = pp.readvar( 'AVG(U)-Z' )[3:]
    uzrms = pp.readvar( 'RMS(U)-Z' )[3:]

