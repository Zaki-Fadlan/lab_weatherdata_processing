import numpy as np
import time
import os
import xarray as xr # Just to get lat/lon for index lookup (or we could save those raw too)

TARGET_LAT = -6.2088
TARGET_LON = 106.8456

def get_nearest_index(lat_array, lon_array, target_lat, target_lon):
    dist = (lat_array - target_lat)**2 + (lon_array - target_lon)**2
    return dist.argmin()

def benchmark_raw():
    print("Benchmarking Raw Binary Array Time Series Extraction...")
    
    data_path = "raw_binary_output/tp_consolidated.dat"
    shape_path = "raw_binary_output/shape.npy"
    
    if not os.path.exists(data_path):
        print("Raw data not found.")
        return

    # Load Metadata
    meta = np.load(shape_path, allow_pickle=True).item()
    shape = meta['shape']
    dtype = meta['dtype']
    
    # We need lat/lon to find the specific index. 
    # For fairness, let's assume we have to read lat/lon from somewhere. 
    # Let's read it from one of the NC files or Zarr just to get the index.
    # We won't count this in the "extraction time" if we assume the application 
    # caches the index for a static grid. But for a fair "cold" test, we should count it?
    # Usually Raw Binary implies you know your grid indices or store them in a separate small raw file.
    # Let's pre-calculate index for the "Pure Read Speed" test, but load coordinates for "Full User Query" test.
    
    # Let's do the "Pure Data Read" benchmark: Assuming we know the index.
    # First, let's get the index once (outside timer/or inside to represent 'lookup cost')
    # If we compare to NetCDF coords lookup, we should probably simulate coordinate lookup or 
    # separate it. The previous NetCDF/Zarr benchmarks INCLUDED coordinate lookup time.
    # So we should include it here too for fairness, or save lat/lon as raw binary too.
    
    # Let's use Zarr just to get index quickly (simulate having a grid file)
    zarr_path = "grib2zarr/batch_tp_output/consolidated.zarr"
    ds = xr.open_dataset(zarr_path, engine='zarr', decode_cf=False)
    if 'latitude' in ds:
         lats = ds['latitude'].values
         lons = ds['longitude'].values
    else:
         lats = ds.coords['latitude'].values
         lons = ds.coords['longitude'].values
         
    idx_flat = get_nearest_index(lats, lons, TARGET_LAT, TARGET_LON)
    
    # For a 3D array [time, lat, lon], memmap usually sees it as flattened or structured.
    # But we saved it as [time, lat, lon].
    # We need to convert flat spatial index to 2D index (lat_idx, lon_idx) if we want to slice properly?
    # Wait, the previous get_nearest_index returns a FLAT index into the 2D lat/lon array.
    # If lat/lon are 2D (grid), then da[:, idx] works in xarray because xarray handles flattening? 
    # No, usually lat/lon are 2D. 
    # Let's check the shape of lat/lon.
    
    is_2d_coords = (lats.ndim == 2)
    if is_2d_coords:
        # Unravel index
        lat_idx, lon_idx = np.unravel_index(idx_flat, lats.shape)
    else:
        # 1D coords
        # If 1D, then we need both indices.
        # But GRIB usually produces 2D lat/lon grids.
        # Let's assume 2D for now based on 'equatorial-southeast-asia' name.
        lat_idx, lon_idx = np.unravel_index(idx_flat, lats.shape)

    # Index Logic
    # If the file is 2D [time, values], we just use the flattened index directly.
    # The previous get_nearest_index returned a flattened index anyway essentially if we look at 1D arrays.
    # But wait, we need to be sure idx_flat matches the 'values' dimension order.
    # cfgrib usually flattens to 'values' if the grid is unstructured or we didn't use decode_cf properly?
    # Or maybe it is just how we opened it.
    
    # BENCHMARK START
    start = time.time()
    
    # 1. Open Memmap
    fp = np.memmap(data_path, dtype=dtype, mode='r', shape=shape)
    
    # 2. Slice
    if len(shape) == 2:
        # [time, values]
        data = fp[:, idx_flat]
    else:
        # [time, lat, lon]
        data = fp[:, lat_idx, lon_idx]
    
    # Force read (memmap is lazy)
    actual_data = np.array(data)
    
    end = time.time()
    
    print(f"Raw Binary (Memmap) Time Series: {end - start:.4f}s")
    print(f"Extracted {len(actual_data)} points.")
    
    # Verify values roughly?
    print(f"First value: {actual_data[0]}")
    return end - start

if __name__ == "__main__":
    benchmark_raw()
