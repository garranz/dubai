import numpy as np
import matplotlib.pyplot as plt

getNs = lambda l_ : np.array( [ 2**i*l for i,l in enumerate(l_) ] )
getInvNs = lambda l_ : np.array( [ 2**(-i)*l for i,l in enumerate(l_) ] )

if __name__ == "__main__":
    # assume that the box is a square
    L = 3463 + 200 # from stl
    h = 645

    dx = 2 # min dx
    levels = [5,5,10,10]
    Nl = len(levels)

    hx = dx * getNs(levels).sum()
    llast = np.round ( (h - hx) / (dx*2**Nl ) )

    levels.append( llast )
    Nl = len(levels)

    Np = ( L / dx )**2 * getInvNs(levels).sum()

    dummy = dx * getNs( levels ).cumsum()
    dummy = np.roll(np.repeat( dummy, 2 ),1)
    dummy[0] = 0
    f1,a1 = plt.subplots()
    a1.plot( Dx:=np.repeat( dx * getNs( [1,]*Nl ) ,2 ), dummy )
    a1.axhline( h_building:=432, ls='--', c='k', lw=.5 )
    a1.set_ylim( 0, dummy[-1]+5 ) 
    a1.set_xlim( 0, Dx[-1]+5 )

    a1.set_xlabel(r'$\Delta \mathit{l}$')
    a1.set_ylabel(r'$y$')
    a1.set_title(rf'$N_p =$ {int(Np):_}')

