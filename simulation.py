import meanderpy as mp # don't forget to pip install
import numpy as np
import matplotlib.pyplot as plt

# fake river (sine)
# replace with real river data???? exciting
x = [i*20 for i in range(500)]
y = [np.sin(xi/500) * 1000 for xi in x]
z = [0 for i in range(500)]

## PARAMS
W = 200 # avg channel width (m)
D = 6 # avg channel depth (m)
nit = 1500 # number of iterations
saved_ts = 20 # save centerline approximation every savedt iterations
deltas = 50 # distance between nodes on centerline
pad = 100 # number of node points along centerline
crdist = 2*W # (normal) distance between two stretches of river for a cutoff to occur (should be function of width?)
depths = D * np.ones((nit,)) # array-like of channel depths. Presumably for each node point?
Cfs = 0.011 * np.ones((nit,)) # array-like of dimensionless Chezy friction factors
kl = 60.0/(365*24*60*60.0) # dimensionless migration rate constant
kv = 1e-12 # vertical slope-dependent erosion rate constant (m/s).
dt = 2*0.05*365*24*60*60.0 # time step in seconds. Should definitely be way more than 1 second
dens = 1000 # density of fluid (kg/m^3) (i think 1000 for pure water)

# initialize Channel object1 for i in range(pad)
channel = mp.Channel(x, y, z, W, D)

# initialize ChannelBelt object (simulation takes place in this thing)
# arguments: list of channels, list of cutoffs, age of channels, age of cutoffs (unsure of how we'd list cutoffs, probably unnecessary for us atm)
channelBelt = mp.ChannelBelt([channel], [], [0.0], [])

# run simulation
channelBelt.migrate(nit, saved_ts, deltas, pad, crdist, depths, Cfs, kl, kv, dt, dens)

# plot simulation
#pb_age is the age at which point bars become covered by vegetation
#ob_age is the "          " oxbow lakes "                            '
#fig = channelBelt.plot('strat')
#plt.show()
channelBelt.create_movie(0, 10000, 'morph', "RiverMeanders/movie.gif")
