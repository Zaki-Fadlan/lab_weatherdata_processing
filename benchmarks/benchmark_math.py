import numpy as np
import time
import os
import struct
import xarray as xr

TARGET_LAT = -6.2088
TARGET_LON = 106.8456

# Known from previous steps, or load dynamically
# SHAPE = (139, 683553)
# DTYPE = float32 (4 bytes)

def get_nearest_index(lat_array, lon_array, target_lat, target_lon):
    dist = (lat_array - target_lat)**2 + (lon_array - target_lon)**2
    return dist.argmin()

def benchmark_math_access():
    print("Benchmarking Mathematical Access (Byte Seeking)...")
    
    data_path = "raw_binary_output/tp_consolidated.dat"
    shape_path = "raw_binary_output/shape.npy"
    
    if not os.path.exists(data_path):
        print("Raw data not found.")
        return

    # Load Metadata to get dimensions
    meta = np.load(shape_path, allow_pickle=True).item()
    shape = meta['shape']
    # Predicted shape: (139, 683553)
    
    num_time_steps = shape[0]
    spatial_width = shape[1] # "Lebar" in valid sense of the flattened array
    
    # Get Index (Simulation of knowing your coordinate index)
    zarr_path = "grib2zarr/batch_tp_output/consolidated.zarr"
    ds = xr.open_dataset(zarr_path, engine='zarr', decode_cf=False)
    if 'latitude' in ds:
         lats = ds['latitude'].values
         lons = ds['longitude'].values
    else:
         lats = ds.coords['latitude'].values
         lons = ds.coords['longitude'].values
         
    target_idx = get_nearest_index(lats, lons, TARGET_LAT, TARGET_LON)
    print(f"Target Flat Index: {target_idx}")
    
    # Mathematical Formula for Offset:
    # Offset = (Time_Index * Spatial_Width + Spatial_Index) * Bytes_Per_Pixel
    bytes_per_pixel = 4 # float32
    
    start = time.time()
    
    extracted_values = []
    
    with open(data_path, "rb") as f:
        for t in range(num_time_steps):
            # Calculate Offset
            # Current Time Plane Start = t * spatial_width
            # Target Pixel = Current Time Plane Start + target_idx
            offset = (t * spatial_width + target_idx) * bytes_per_pixel
            
            # Seek
            f.seek(offset)
            
            # Read 4 bytes
            bytes_val = f.read(4)
            
            # Unpack
            val = struct.unpack('f', bytes_val)[0]
            extracted_values.append(val)
            
    end = time.time()
    
    print(f"Mathematical Access Time: {end - start:.4f}s")
    print(f"Extracted {len(extracted_values)} points.")
    print(f"First value: {extracted_values[0]}")
    return end - start

if __name__ == "__main__":
    benchmark_math_access()
