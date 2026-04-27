import meanderpy as mp
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.ops import linemerge

## IMPORTANT: must first extract centerline data using centerlineExtraction[1/2].py


## **PARAMS**
W = 175*12*2.54/100 # (175 ft) avg channel width (m) GUESSTIMATED FROM GOOGLE MAPS
D = 4*12*2.54/100 # (4ft) avg channel depth (m) TAKEN FROM RANDOM FORUM THREAD [https://www.dragonsfoot.org/forums/viewtopic.php?t=58804]
nit = 4300 # number of iterations
saved_ts = 20 # save centerline approximation every savedt iterations
deltas = W/2 # distance between nodes on centerline
pad = 20 # affects straight channel padding at both ends of the river segment of interest. large padding = more straight channel assumed at both ends
crdist = 2*W # (normal) distance between two stretches of river for a cutoff to occur (should be function of width)
depths = D * np.ones((nit,)) # array-like of channel depths. Presumably for each node point?
Cfs = 0.011 * np.ones((nit,)) # array-like of dimensionless Chezy friction factors
kl = 1.2e-7 # dimensionless migration rate constant
kv = 1e-12 # vertical slope-dependent erosion rate constant (m/s).
dt = 0.01*365*24*60*60.0 # time step in seconds. currently 0.01 years
dens = 1000 # density of fluid (kg/m^3) (currently for pure water)

## **LOAD DATA**
print("beginning data extraction from file")
## Read centerline data from file and do some coordinate conversion (I don't really know how this works)

## Load 1980 data {
# the number after epsg might need to change if location changes
filename = 'arkansasCenterlineUSGS1980.geojson'
gdf = gpd.read_file(filename).to_crs(epsg=32613)

# the json file has nine rows for some reason so this merges them into one line
data = linemerge(gdf.explode(index_parts=False).geometry.tolist())

# interpolate evenly spaced points along the centerline
# if a number other than deltas is passed the simulation only does part of the river for some reason
distances = np.arange(0, data.length, deltas)
interpolatedPoints = [data.interpolate(d) for d in distances]

# build tidy x and y arrays
xOld = np.array([pt.x for pt in interpolatedPoints])
yOld = np.array([pt.y for pt in interpolatedPoints])

# make sure river is flowing correct direction (this assumes west to east. for rivers flowing east to west, the check should go the other way)
if xOld[0] > xOld[-1]:
    xOld = xOld[::-1]
    yOld = yOld[::-1]

## Load 2023 data (works the same way)
filename = 'arkansasCenterlineUSGS2023.geojson'
gdf = gpd.read_file(filename).to_crs(epsg=32613)
data = linemerge(gdf.explode(index_parts=False).geometry.tolist())
distances = np.arange(0, data.length, deltas)
interpolatedPoints = [data.interpolate(d) for d in distances]
xNew = np.array([pt.x for pt in interpolatedPoints])
yNew = np.array([pt.y for pt in interpolatedPoints])
if xNew[0] > xNew[-1]:
    xNew = xNew[::-1]
    yNew = yNew[::-1]

# normalize xOld and yOld arrays as they had huge values which was making stuff crash
xOld = xOld - xOld[0]
yOld = yOld - yOld[0]
xNew = xNew - xNew[0]
yNew = yNew - yNew[0]

# bound the old data (which we have more of) by the region of new data (so both pieces of data cover the same region)
offset = 0
for i in range(len(xOld)):
    if(not (xNew[0] <= xOld[i - offset] and xOld[i - offset] <= xNew[-1])):
        xOld = np.delete(xOld, i - offset)
        yOld = np.delete(yOld, i - offset)
        offset += 1

# plot old & new data on same axes
plt.plot(xOld, yOld)
plt.axis('scaled')
plt.plot(xNew, yNew)
plt.title("Planforms of the Arkansas River east of Pueblo")
plt.legend(['1980', '2023'], loc='upper center', prop={'size': 8})
plt.savefig('initPlotCombined.png') # I like this better than plot.show() since I can look at the graph while the simulation is running

# plot just old data
plt.clf()
plt.plot(xOld, yOld)
plt.axis('scaled')
plt.title("1980 Arkansas River planform")
plt.savefig('initPlot1980.png')

# plot just new data
plt.clf()
plt.plot(xNew, yNew)
plt.axis('scaled')
plt.title("2023 Arkansas River planform")
plt.savefig('initPlot2023.png')

# estimate at z values
startElev = 1430.0 # estimating starting elevation as 1430 meters which is the elevation of Pueblo
avgSlope = 0.0026 # global average stream gradient is 2.6m/km
z = np.zeros(len(xOld))
z[0] = startElev
for i in range(1, len(xOld)):
    # find elevation of point i by finding distance from point i-1
    # and multiplying by slope (works well as rough estimate but assumes the river has constant gradient (in magnitude))
    stepDist = np.sqrt((xOld[i] - xOld[i-1])**2 + (yOld[i] - yOld[i-1])**2)
    z[i] = z[i-1] - avgSlope*stepDist

print(f"data read. beginning simulation")

## **SIMULATION**
# initialize Channel object
channel = mp.Channel(xOld, yOld, z, W, D)

# initialize ChannelBelt object (simulation takes place in this thing)
# arguments: list of channels, list of cutoffs, age of channels, age of cutoffs (unsure of how we'd list cutoffs, probably unnecessary for us atm)
channelBelt = mp.ChannelBelt([channel], [], [0.0], [])

# run simulation
channelBelt.migrate(nit, saved_ts, deltas, pad, crdist, depths, Cfs, kl, kv, dt, dens)

print('simulation complete. saving results ...')
         
# plot final estimate
fig = channelBelt.plot('age')
plt.savefig('finalPlot.png')
print('resultant png saved.')

# and/or plot entire simulation as gif
channelBelt.create_movie(0, 10000, 'strat', "movie.gif")
print('resultant gif saved.')

print('enjoy your freshly meandered river')
