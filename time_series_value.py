import xarray as xr
import numpy as np
import os
import pandas as pd

def extract_jakarta_series():
    # Jakarta Coordinates
    target_lat = -6.2088
    target_lon = 106.8456
    location_name = "Jakarta"
    
    print(f"Extracting time series for {location_name} ({target_lat}, {target_lon})...")
    
    # We want 100m wind (dataset_1) and maybe 10m wind (dataset_2) for comparison
    zarr_upper = "zarr_output/dataset_1_heightAboveGround_instant.zarr"
    
    data_frames = []
    
    # 1. Extract Upper Air Winds (80m, 100m)
    if os.path.exists(zarr_upper):
        ds = xr.open_zarr(zarr_upper, consolidated=True)
        
        # Find nearest point
        lats = ds['latitude'].values if 'latitude' in ds else ds['lat'].values
        lons = ds['longitude'].values if 'longitude' in ds else ds['lon'].values
        
        dist_sq = (lats - target_lat)**2 + (lons - target_lon)**2
        min_idx = np.argmin(dist_sq)
        
        # Select spatial point
        # ds contains 'step' dimension and 'values' dimension (flattened space)
        # We perform selection on 'values' index
        ds_point = ds.isel(values=min_idx)
        
        # Extract u and v for all steps and levels
        # Dimensions are likely (step, heightAboveGround)
        # Check dims
        levels = ds['heightAboveGround'].values
        
        # Prepare lists
        steps = ds['step'].values
        # Calculate times manually to be robust against metadata issues
        # Filenames confirmed f000, f001, etc. -> Hourly data
        if 'time' in ds:
             # ds['time'] might be a scalar or array
             base_time = ds['time'].values
             if base_time.ndim > 0:
                 base_time = base_time[0]
        else:
             # Fallback to filename parsing or hardcoded if needed, but time should be there
             # Based on user context: 2026-01-28
             print("Warning: 'time' coord missing, using default start.")
             base_time = np.datetime64('2026-01-28T00:00:00')

        print(f"Found {len(steps)} time steps. Base time: {base_time}")
        
        for i, step in enumerate(steps):
            # Force hourly increment
            t = base_time + np.timedelta64(i, 'h')
            
            # For each level
            for j, lev in enumerate(levels):
                u = ds_point['u'].isel(step=i, heightAboveGround=j).values
                v = ds_point['v'].isel(step=i, heightAboveGround=j).values
                speed = np.sqrt(u**2 + v**2)
                
                data_frames.append({
                    'Step': i,
                    'Time': t,
                    'Level': int(lev),
                    'U': float(u),
                    'V': float(v),
                    'Speed': float(speed)
                })
    else:
        print(f"Warning: {zarr_upper} not found.")

    # Create DataFrame
    df = pd.DataFrame(data_frames)
    
    # Sort
    df = df.sort_values(['Step', 'Level'])
    
    # Display snippet
    print("\n--- Time Series Data (Top 10 rows) ---")
    print(df.head(10).to_string(index=False))
    
    print("\n--- Time Series Data (Last 10 rows) ---")
    print(df.tail(10).to_string(index=False))
    
    # Check for NaN or weird jumps
    if df.isnull().values.any():
        print("\n[!] WARNING: NaNs detected in the data.")
    else:
        print("\nAll data points are valid (no NaNs).")
        
    # Save to CSV
    csv_name = "jakarta_wind_profile.csv"
    df.to_csv(csv_name, index=False)
    print(f"\nFull time series saved to {csv_name}")

if __name__ == "__main__":
    extract_jakarta_series()
