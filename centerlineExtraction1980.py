import pynhd
from shapely.geometry import box
import os

bounds = (-104.54089, 38.25403, -104.44024, 38.27055)

# connects to the NHDPlus High Resolution flowline database (I don't know how this works)
bigData = pynhd.WaterData("nhdflowline_network")

# only find river data in our area of concern
boundedData = bigData.bybox(bounds)

# boundedData has info for all water features in area
# filter for the Arkansas
arkansas = boundedData[boundedData['gnis_name'] == 'Arkansas River']

# this if/else was useful for debugging but also could be a useful sanity check if we ever decide to use another location
if not arkansas.empty:
    arkansas.to_file('arkansasCenterlineUSGS1980.geojson', driver='GeoJSON')
    print("Found and saved data successfully")
else:
    print("No data found for given river in given bounds")

os.remove('arkansas_high_res.tif')