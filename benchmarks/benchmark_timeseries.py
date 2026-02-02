import xarray as xr
import time
import glob
import numpy as np

TARGET_LAT = -6.2088
TARGET_LON = 106.8456

def get_nearest_index(lat_array, lon_array, target_lat, target_lon):
    dist = (lat_array - target_lat)**2 + (lon_array - target_lon)**2
    return dist.argmin()

def benchmark_timeseries_netcdf():
    # Approach 1: Open 140 separate files (MFDataset)
    files = sorted(glob.glob("grib2netcdf/batch_output/*.nc"))
    if not files:
        print("No batch NetCDF files found.")
        return
    
    print(f"Benchmarking NetCDF MFDataset ({len(files)} files)...")
    start = time.time()
    
    # open_mfdataset lazy loads
    with xr.open_mfdataset(files, engine='netcdf4', combine='nested', concat_dim='step', decode_cf=False) as ds:
        # Find index (assuming same grid for all, read from first)
        # Accessing coords might trigger open of first file
        if 'latitude' in ds:
            lats = ds['latitude'].values[0] if ds['latitude'].ndim > 1 else ds['latitude'].values
            lons = ds['longitude'].values[0] if ds['longitude'].ndim > 1 else ds['longitude'].values
        else:
            # Fallback if coords are variables
             lats = ds['latitude'].values
             lons = ds['longitude'].values
             
        idx = get_nearest_index(lats, lons, TARGET_LAT, TARGET_LON)
        
        # Extract Time Series
        # Variable name? Pick the last one
        var_name = list(ds.data_vars)[-1]
        
        # Slice: all time, specific index
        # This triggers reading from 140 files
        data = ds[var_name][:, idx].values
        
    end = time.time()
    print(f"NetCDF MFDataset Time Series: {end - start:.4f}s")
    print(f"Extracted {len(data)} points.")

def benchmark_timeseries_zarr():
    # Approach 2: Open single consolidated Zarr
    zarr_path = "grib2zarr/batch_output/consolidated.zarr"
    
    print(f"Benchmarking Consolidated Zarr...")
    start = time.time()
    
    with xr.open_dataset(zarr_path, engine='zarr') as ds:
        if 'latitude' in ds:
             lats = ds['latitude'].values
             lons = ds['longitude'].values
        else:
             # Try coords
             lats = ds.coords['latitude'].values
             lons = ds.coords['longitude'].values
             
        idx = get_nearest_index(lats, lons, TARGET_LAT, TARGET_LON)
        
        var_name = list(ds.data_vars)[-1]
        
        # Slice
        data = ds[var_name][:, idx].values
        
    end = time.time()
    print(f"Consolidated Zarr Time Series: {end - start:.4f}s")
    print(f"Extracted {len(data)} points.")

if __name__ == "__main__":
    print(f"Benchmarking Time Series Extraction at Jakarta: {TARGET_LAT}, {TARGET_LON}")
    benchmark_timeseries_netcdf()
    benchmark_timeseries_zarr()
