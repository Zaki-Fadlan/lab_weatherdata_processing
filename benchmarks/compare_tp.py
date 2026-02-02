import xarray as xr
import glob
import numpy as np
import pandas as pd
import time
import os

TARGET_LAT = -6.2088
TARGET_LON = 106.8456

def get_nearest_index(lat_array, lon_array, target_lat, target_lon):
    dist = (lat_array - target_lat)**2 + (lon_array - target_lon)**2
    return dist.argmin()

def compare_tp():
    print(f"Comparing 'tp' at Jakarta: {TARGET_LAT}, {TARGET_LON}")
    
    # 1. NetCDF (Separate Files)
    nc_files = sorted(glob.glob("grib2netcdf/batch_tp_output/*.nc"))
    if not nc_files:
        print("No NetCDF files found in grib2netcdf/batch_tp_output/")
        return

    print(f"Reading {len(nc_files)} NetCDF files...")
    
    # Use decode_cf=False to match how we created the consolidated zarr and avoid errors
    # We will manually handle time if needed
    try:
        with xr.open_mfdataset(nc_files, engine='netcdf4', combine='nested', concat_dim='step', decode_cf=False) as ds_nc:
            # Get Coords
            if 'latitude' in ds_nc:
                lats = ds_nc['latitude'].values[0] if ds_nc['latitude'].ndim > 1 else ds_nc['latitude'].values
                lons = ds_nc['longitude'].values[0] if ds_nc['longitude'].ndim > 1 else ds_nc['longitude'].values
            else:
                 lats = ds_nc.coords['latitude'].values
                 lons = ds_nc.coords['longitude'].values
                 
            idx = get_nearest_index(lats, lons, TARGET_LAT, TARGET_LON)
            
            # Extract
            # Variable should be 'tp'
            if 'tp' in ds_nc:
                tp_nc = ds_nc['tp'][:, idx].values
            else:
                # Fallback check
                print(f"Vars in NC: {list(ds_nc.data_vars)}")
                var_name = list(ds_nc.data_vars)[-1]
                tp_nc = ds_nc[var_name][:, idx].values
                
            # Try to get time
            # valid_time usually exists
            if 'valid_time' in ds_nc:
                times_nc = ds_nc['valid_time'].values
            else:
                times_nc = np.arange(len(tp_nc)) # Dummy

    except Exception as e:
        print(f"Error reading NetCDF: {e}")
        return

    # 2. Zarr (Consolidated)
    zarr_path = "grib2zarr/batch_tp_output/consolidated.zarr"
    if not os.path.exists(zarr_path):
        print("Zarr path not found.")
        return
        
    print("Reading Consolidated Zarr...")
    try:
        with xr.open_dataset(zarr_path, engine='zarr', decode_cf=False) as ds_zarr:
            # We assume same grid, verify?
            # Just use same index logic or reuse index if grid is guaranteed same
            # Reread coords to be safe
            if 'latitude' in ds_zarr:
                lats_z = ds_zarr['latitude'].values
                lons_z = ds_zarr['longitude'].values
            else:
                 lats_z = ds_zarr.coords['latitude'].values
                 lons_z = ds_zarr.coords['longitude'].values
            
            idx_z = get_nearest_index(lats_z, lons_z, TARGET_LAT, TARGET_LON)
            
            if 'tp' in ds_zarr:
                tp_zarr = ds_zarr['tp'][:, idx_z].values
            else:
                var_name = list(ds_zarr.data_vars)[-1]
                tp_zarr = ds_zarr[var_name][:, idx_z].values
                
    except Exception as e:
        print(f"Error reading Zarr: {e}")
        return
        
    # Compare
    # Convert times to readable if they are epoch
    # Assuming valid_time is seconds from epoch? Or something else?
    # GRIB valid_time is typically epoch seconds.
    timestamps = pd.to_datetime(times_nc, unit='s')
    
    df = pd.DataFrame({
        'Timestamp': timestamps,
        'NetCDF_Value': tp_nc,
        'Zarr_Value': tp_zarr,
        'Difference': tp_nc - tp_zarr
    })
    
    print("\n--- Comparison Results (Head) ---")
    print(df.head())
    
    print("\n--- Comparison Results (Tail) ---")
    print(df.tail())
    
    # Check equality
    is_close = np.allclose(tp_nc, tp_zarr, equal_nan=True)
    print(f"\nAre values identical (within tolerance)? {is_close}")
    if not is_close:
        print(f"Max difference: {np.nanmax(np.abs(tp_nc - tp_zarr))}")

if __name__ == "__main__":
    compare_tp()
