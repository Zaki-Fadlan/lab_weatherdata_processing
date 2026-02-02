import xarray as xr
import time
import glob
import numpy as np
import os

TARGET_LAT = -6.2088
TARGET_LON = 106.8456

def get_nearest_index(lat_array, lon_array, target_lat, target_lon):
    dist = (lat_array - target_lat)**2 + (lon_array - target_lon)**2
    return dist.argmin()

def benchmark_tp_netcdf():
    files = sorted(glob.glob("grib2netcdf/batch_tp_output/*.nc"))
    if not files:
        print("No NetCDF files found in grib2netcdf/batch_tp_output/")
        return
    
    print(f"Benchmarking NetCDF MFDataset (TP) - {len(files)} files...")
    start = time.time()
    
    # decode_cf=False for fairer/safer comparison given previous encoding issues
    with xr.open_mfdataset(files, engine='netcdf4', combine='nested', concat_dim='step', decode_cf=False) as ds:
        # Get Coords (cached/from first file)
        # Assuming lat/lon present as data variables or coords
        if 'latitude' in ds:
             lats = ds['latitude'].values[0] if ds['latitude'].ndim > 1 else ds['latitude'].values
             lons = ds['longitude'].values[0] if ds['longitude'].ndim > 1 else ds['longitude'].values
        else:
             lats = ds.coords['latitude'].values
             lons = ds.coords['longitude'].values
             
        idx = get_nearest_index(lats, lons, TARGET_LAT, TARGET_LON)
        
        # Extract Time Series
        if 'tp' in ds:
            data = ds['tp'][:, idx].values
        else:
            # Fallback if renamed or different
            var_name = list(ds.data_vars)[-1] # likely tp if it's the only one
            data = ds[var_name][:, idx].values
            
    end = time.time()
    print(f"NetCDF MFDataset (TP): {end - start:.4f}s")
    print(f"Extracted {len(data)} points.")
    return end - start

def benchmark_tp_zarr():
    zarr_path = "grib2zarr/batch_tp_output/consolidated.zarr"
    if not os.path.exists(zarr_path):
        print("Zarr path not found.")
        return
    
    print(f"Benchmarking Consolidated Zarr (TP)...")
    start = time.time()
    
    with xr.open_dataset(zarr_path, engine='zarr', decode_cf=False) as ds:
        if 'latitude' in ds:
             lats = ds['latitude'].values
             lons = ds['longitude'].values
        else:
             lats = ds.coords['latitude'].values
             lons = ds.coords['longitude'].values
             
        idx = get_nearest_index(lats, lons, TARGET_LAT, TARGET_LON)
        
        if 'tp' in ds:
            data = ds['tp'][:, idx].values
        else:
            var_name = list(ds.data_vars)[-1]
            data = ds[var_name][:, idx].values
        
    end = time.time()
    print(f"Consolidated Zarr (TP): {end - start:.4f}s")
    print(f"Extracted {len(data)} points.")
    return end - start

if __name__ == "__main__":
    print(f"Benchmarking 'tp' Time Series at Jakarta: {TARGET_LAT}, {TARGET_LON}")
    t_nc = benchmark_tp_netcdf()
    t_zarr = benchmark_tp_zarr()
    
    if t_nc and t_zarr:
        print(f"\nSummary:")
        print(f"NetCDF: {t_nc:.4f}s")
        print(f"Zarr:   {t_zarr:.4f}s")
        print(f"Zarr is {t_nc / t_zarr:.1f}x faster")
