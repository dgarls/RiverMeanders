import ee
import geemap
import cv2
import numpy as np
import rasterio
import geopandas as gpd
import os
import sys
from shapely.geometry import LineString
from skimage.morphology import skeletonize

# version check (certain packages are incompatable with new numpy versions)
if int(np.__version__.split('.')[0]) >= 2:
    print(f"error: NumPy version {np.__version__} is incompatible.")
    print("running \"pip install 'numpy<2'\" will solve this issue but possibly break other things with your python package dependencies")
    sys.exit(1)

ee.Authenticate()
ee.Initialize(project='arkansas-493219') # this links to my personal google earth stuff and likely won't work on someone else's computer?

# define region of interest
roi = ee.Geometry.Rectangle([-104.54089, 38.25403, -104.44024, 38.27055])

# download .tif image of the region of interest
s2_col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
         .filterBounds(roi)
         .filterDate('2023-05-01', '2023-09-30')
         .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10)))
native_proj = s2_col.first().select('B3').projection()
img = s2_col.median().clip(roi)
mndwi = img.normalizedDifference(['B3', 'B11']).rename('MNDWI')
geemap.ee_export_image(mndwi, filename='arkansas_high_res.tif', scale=10, region=roi, crs=native_proj)

# get binary mask of the river
with rasterio.open('arkansas_high_res.tif') as src:
    data = src.read(1)
    transform = src.transform
    crs = src.crs
data = np.nan_to_num(data)
data_norm = cv2.normalize(data, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
_, binary_mask = cv2.threshold(data_norm, 150, 255, cv2.THRESH_BINARY)
kernel = np.ones((9,9), np.uint8) 
clean_mask = cv2.dilate(binary_mask, kernel, iterations=1)
clean_mask = cv2.erode(clean_mask, kernel, iterations=1)

# thin river profile to single pixel
skeleton = skeletonize(clean_mask > 0)

# vectorize thin river profile
rows, cols = np.where(skeleton)
points = [transform * (c, r) for r, c in zip(rows, cols)]
points.sort(key=lambda p: p[0]) # starts at the west end

sorted_points = []
current_pt = points.pop(0)
sorted_points.append(current_pt)

while len(points) > 0:
    distances = [((p[0]-current_pt[0])**2 + (p[1]-current_pt[1])**2) for p in points]
    closest_idx = np.argmin(distances)
    dist = np.sqrt(distances[closest_idx])
    
    if dist < 300: # can mess with this value if we're getting extra/not enough river
        current_pt = points.pop(closest_idx)
        sorted_points.append(current_pt)
    else:
        # If we hit a massive gap (>300m), check if we have enough river yet
        if len(sorted_points) > 500: # Adjust based on expected node count
            #print(f"Large gap reached. Ending reach at {len(sorted_points)} points.")
            break 
        else:
            # If we haven't found the 'main' river yet, keep looking
            current_pt = points.pop(closest_idx)
            sorted_points = [current_pt]

# export results
line = LineString(sorted_points)
gdf = gpd.GeoDataFrame(index=[0], crs=crs, geometry=[line])
gdf.to_file('arkansasCenterlineUSGS2023.geojson', driver='GeoJSON')
os.remove('arkansas_high_res.tif')
print("Found and saved data successfully")