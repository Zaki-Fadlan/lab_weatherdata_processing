import xarray as xr
import numpy as np
import time
import glob
import os

TARGET_LAT = -6.2088
TARGET_LON = 106.8456

def get_nearest_index(lat_array, lon_array, target_lat, target_lon):
    dist = (lat_array - target_lat)**2 + (lon_array - target_lon)**2
    return np.argmin(dist)

def benchmark_spatial(file_paths, engine, n_files=None):
    if not file_paths:
        return 0, 0
    
    # Limit number of files if needed
    if n_files:
        file_paths = file_paths[:n_files]
        
    start_time = time.time()
    count = 0
    
    # Pre-calculate index from the first file to simulate "Hot Access"
    # We assume all files share the same grid structure for this test
    # (which they do, as they come from the same GRIB)
    
    # 1. Warm up / Find Index cost
    first_path = file_paths[0]
    kwargs = {'engine': engine}
    if engine == 'netcdf4':
         kwargs['decode_cf'] = False

    t0 = time.time()
    with xr.open_dataset(first_path, **kwargs) as ds:
        # Load coords
        # In the NetCDF output we saw, lat/lon are data variables, not coords, 
        # but xarray might have loaded them.
        # We need to access them by name.
        if 'latitude' in ds:
            lats = ds['latitude'].values
            lons = ds['longitude'].values
        elif 'latitude' in ds.coords:
            lats = ds.coords['latitude'].values
            lons = ds.coords['longitude'].values
        else:
            # Fallback for safe access if structure varies
            print(f"Computed index failed: latitude/longitude not found in {first_path}")
            return 0, 0

        idx = get_nearest_index(lats, lons, TARGET_LAT, TARGET_LON)
    
    t_index = time.time() - t0
    print(f"[{engine}] Index finding time: {t_index:.4f}s (Index: {idx})")

    # 2. Benchmark Hot Access (Reading value at index)
    t_access_start = time.time()
    for file_path in file_paths:
        try:
            with xr.open_dataset(file_path, **kwargs) as ds:
                # Read the first data variable at the specific index
                # identifying data vars (excluding lat/lon/time etc if they are data vars)
                # We simply pick the last variable which is likely the weather parameter
                var_name = list(ds.data_vars)[-1]
                # If var is lat or lon, pick another one
                if var_name in ['latitude', 'longitude', 'time', 'step', 'valid_time'] and len(ds.data_vars) > 1:
                     # iterate to find a real variable
                     for v in ds.data_vars:
                         if v not in ['latitude', 'longitude', 'time', 'step', 'valid_time']:
                             var_name = v
                             break
                
                # Access simple value
                val = ds[var_name][idx].values
                count += 1
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    total_time = time.time() - t_access_start
    return total_time, count

if __name__ == "__main__":
    
    print(f"Benchmarking access at Jakarta: {TARGET_LAT}, {TARGET_LON}")

    # NetCDF
    print("\n--- NetCDF ---")
    netcdf_files = sorted(glob.glob("grib2netcdf/output/*.nc"))
    # Run only on files that actually have the grid (all of them should)
    nc_time, nc_count = benchmark_spatial(netcdf_files, engine="netcdf4")
    if nc_count > 0:
        print(f"NetCDF: Accessed {nc_count} files in {nc_time:.4f} seconds.")
        print(f"NetCDF Avg per file: {nc_time/nc_count:.4f} s")

    # Zarr
    print("\n--- Zarr ---")
    zarr_files = sorted(glob.glob("grib2zarr/output/*.zarr"))
    zarr_time, zarr_count = benchmark_spatial(zarr_files, engine="zarr")
    if zarr_count > 0:
        print(f"Zarr: Accessed {zarr_count} stores in {zarr_time:.4f} seconds.")
        print(f"Zarr Avg per file: {zarr_time/zarr_count:.4f} s")
