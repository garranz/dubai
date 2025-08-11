import numpy as np
import sys

# ======= Parameters =============
z0 = 0.0002   # Surface roughness length
u_star = 0.5  # Friction velocity
k = 0.4       # von Karman constant
#=================================

def wind_profile(z_, z0_, u_star_, k_):
    """
    Computes the wind speed at height z in the atmospheric boundary layer
    using the logarithmic wind profile.

    Parameters:
    - z : height above ground (m)
    - z0 : roughness length (m)
    - u_star : friction velocity (m/s)
    - k : von Karman constant (~0.4)

    Returns:
    - u : wind speed at height z (m/s)
    """
    return (u_star_ / k_) * np.log(z_ / z0_)

def write_abl_profile(N: int, ztop: float= 650.):

    heights = np.linspace(.1, ztop, N)  # heights from .1 m to ztop m
    u = np.zeros_like(heights)

    filename = 'wind_profile.txt'
    # Write to file
    with open(filename, 'w') as f:
        for i, z in enumerate(heights):
            if z > 0:

                u_ = wind_profile(z, z0, u_star, k)
                f.write(f"{z:.5f} {u_:.5f}\n")
                u[i] = u_

    return heights, u


if __name__ == "__main__":
    write_abl_profile( int(sys.argv[1]) )

