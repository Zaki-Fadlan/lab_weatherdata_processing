import xarray as xr
import numpy as np
import pandas as pd

TARGET_LAT = -6.2088
TARGET_LON = 106.8456

def verify_t2m():
    zarr_path = 'zarr_output/dataset_0_0_instant.zarr'
    print(f"Opening {zarr_path}...")
    
    try:
        ds = xr.open_dataset(zarr_path, engine='zarr', decode_cf=True)
    except Exception as e:
        print(f"Failed to open Zarr: {e}")
        return

    if 't2m' not in ds:
        print("Variable 't2m' not found in this dataset.")
        print("Available variables:", list(ds.data_vars))
        return

    # Find nearest point
    # Assuming flattened 'values' dimension or 2D lat/lon.
    # Based on previous steps, it seemed to consist of 1D 'values' with coordinate arrays.
    
    if 'latitude' in ds:
         lats = ds['latitude'].values
         lons = ds['longitude'].values
    else:
         lats = ds.coords['latitude'].values
         lons = ds.coords['longitude'].values
         
    dist = (lats - TARGET_LAT)**2 + (lons - TARGET_LON)**2
    nearest_idx = dist.argmin()
    
    print(f"Nearest Index: {nearest_idx}")
    print(f"Lat/Lon at index: {lats[nearest_idx]:.4f}, {lons[nearest_idx]:.4f}")
    
    # Extract Time Series
    # Handle dimensions: likely (step, values) or (time, values)
    # The 'step' dimension usually acts as time here.
    
    t2m_series = ds['t2m'][:, nearest_idx]
    
    # Get timestamps
    # Often 'valid_time' or 'time' + 'step'
    # ds.coords['valid_time'] should exist if cfgrib created it.
    
    if 'valid_time' in ds:
        timestamps = ds['valid_time'].values
        # Convert to readable if needed (often numpy datetime64)
        timestamps = pd.to_datetime(timestamps)
    elif 'time' in ds and 'step' in ds:
        # Construct validity time
        base_time = ds['time'].values
        steps = ds['step'].values
        # This might be tricky if base_time is scalar and step is array
        # Let's verify what we have access to.
        try:
             timestamps = pd.to_datetime(ds['valid_time'].values)
        except:
             timestamps = np.arange(len(t2m_series)) # Fallback
    else:
        timestamps = np.arange(len(t2m_series))

    print(f"\n--- T2M Data for Jakarta ({TARGET_LAT}, {TARGET_LON}) ---")
    print(f"Total Time Steps: {len(t2m_series)}")
    
    df = pd.DataFrame({'Timestamp': timestamps, 'T2M (K)': t2m_series.values})
    # Add Celsius for convenience
    df['T2M (C)'] = df['T2M (K)'] - 273.15
    
    print(df.head(10))
    print("...")
    print(df.tail(5))

if __name__ == "__main__":
    verify_t2m()
