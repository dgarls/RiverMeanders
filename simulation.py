import meanderpy as mp
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.ops import linemerge

## IMPORTANT: must first extract centerline data using centerlineExtraction.py

## **PARAMS**
W = 175*12*2.54/100 # avg channel width (m) GUESSTIMATED FROM GOOGLE MAPS
D = 4*12*2.54/100 # avg channel depth (m) TAKEN FROM RANDOM FORUM THREAD [https://www.dragonsfoot.org/forums/viewtopic.php?t=58804]
nit = 1500 # number of iterations
saved_ts = 20 # save centerline approximation every savedt iterations
deltas = W/2 # distance between nodes on centerline
pad = 20 # affects straight channel padding at both ends of the river segment of interest. large padding = more straight channel assumed at both ends
crdist = 2*W # (normal) distance between two stretches of river for a cutoff to occur (should be function of width?)
depths = D * np.ones((nit,)) # array-like of channel depths. Presumably for each node point?
Cfs = 0.011 * np.ones((nit,)) # array-like of dimensionless Chezy friction factors
kl = 60.0/(365*24*60*60.0) # dimensionless migration rate constant
kv = 1e-12 # vertical slope-dependent erosion rate constant (m/s).
dt = 0.01*365*24*60*60.0 # time step in seconds. Should definitely be way more than 1 second
dens = 1000 # density of fluid (kg/m^3) (currently for pure water)

## **LOAD DATA**
## Read centerline data from file and do some coordinate conversion (I don't really know how this works)
print("beginning data extraction from file")
# the number after epsg might need to change for a different location
filename = 'arkansasCenterlineUSGS.geojson'
gdf = gpd.read_file(filename).to_crs(epsg=32613)

# the json file has nine rows for some reason so this merges them into one line
data = linemerge(gdf.explode(index_parts=False).geometry.tolist())

# interpolate evenly spaced points along the centerline
# if a number other than deltas is passed the simulation only does part of the river for some reason
distances = np.arange(0, data.length, deltas)
interpolatedPoints = [data.interpolate(d) for d in distances]

# build tidy x and y arrays
x = np.array([pt.x for pt in interpolatedPoints])
y = np.array([pt.y for pt in interpolatedPoints])

# normalize x and y arrays as they had huge values which was making stuff crash
x = x - x[0]
y = y - y[0]

if x[0] > x[-1]:
    print("Reversing arrays: River was flowing East to West!")
    x = x[::-1]
    y = y[::-1]

# show initial state of the river
plt.plot(x, y)
plt.axis('scaled')
plt.savefig('initPlot.png') # I like this better than plot.show() since I can look at the graph while the simulation is running

# estimate at z values
# estimating starting elevation as 1430 meters which is the elevation of Pueblo
# global average stream gradient is 2.6m/km
startElev = 1430.0
avgSlope = 0.0026
z = np.zeros(len(x))
z[0] = startElev
for i in range(1, len(x)):
    # find elevation of point i by finding distance from point i-1
    # and multiplying by slope (works well as rough estimate but assumes linearity)
    stepDist = np.sqrt((x[i] - x[i-1])**2 + (y[i] - y[i-1])**2)
    z[i] = z[i-1] - avgSlope*stepDist


print(f"data read. beginning simulation")



## **SIMULATION**
# initialize Channel object
channel = mp.Channel(x, y, z, W, D)

# initialize ChannelBelt object (simulation takes place in this thing)
# arguments: list of channels, list of cutoffs, age of channels, age of cutoffs (unsure of how we'd list cutoffs, probably unnecessary for us atm)
channelBelt = mp.ChannelBelt([channel], [], [0.0], [])

# run simulation
channelBelt.migrate(nit, saved_ts, deltas, pad, crdist, depths, Cfs, kl, kv, dt, dens)

print('simulation complete. saving results ...')
         
# plot final estimate
fig = channelBelt.plot('strat')
plt.savefig('finalPlot.png')
print('resultant png saved.')

# and/or plot entire simulation as gif
channelBelt.create_movie(0, 10000, 'strat', "movie.gif")
print('resultant gif saved.')

print('enjoy your freshly meandered river')
