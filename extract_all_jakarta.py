import xarray as xr
import pandas as pd
import numpy as np
import glob
import os
import warnings
from datetime import datetime, timedelta

warnings.filterwarnings('ignore')

def extract_jakarta_data():
    # consistent Jakarta coordinates
    LAT = -6.2088
    LON = 106.8456
    
    zarr_dir = "zarr_output"
    output_csv = "jakarta_complete_weather.csv"
    
    zarr_stores = sorted(glob.glob(os.path.join(zarr_dir, "*.zarr")))
    print(f"Found {len(zarr_stores)} Zarr stores.")
    
    all_data = []
    
    # Base time for reconstruction if needed
    BASE_TIME_STR = "2026-01-28 00:00:00"
    base_dt = pd.to_datetime(BASE_TIME_STR)
    
    for zarr_path in zarr_stores:
        store_name = os.path.basename(zarr_path)
        # Infer bundle from filename if possible: "bundle_dataset_..."
        bundle = store_name.split('_')[0] if '_' in store_name else 'unknown'
        
        try:
            ds = xr.open_zarr(zarr_path, consolidated=True)
            
            # Robust Nearest Neighbor Selection
            if 'latitude' in ds.coords and 'longitude' in ds.coords:
                lats = ds['latitude'].values
                lons = ds['longitude'].values
                
                if lats.ndim == 1 and lons.ndim == 1:
                    # 1D Grid (Rectilinear)
                    lat_idx = int(np.abs(lats - LAT).argmin())
                    lon_idx = int(np.abs(lons - LON).argmin())
                    # ds.isel expects dimension names. Assuming dim name matches coord name for 1D
                    # If dims are different (e.g. y, x), we need to check ds['latitude'].dims
                    lat_dim = ds['latitude'].dims[0]
                    lon_dim = ds['longitude'].dims[0]
                    ds_point = ds.isel({lat_dim: lat_idx, lon_dim: lon_idx})
                
                elif lats.ndim == 2 and lons.ndim == 2:
                    # 2D Grid (Curvilinear)
                    dist = (lats - LAT)**2 + (lons - LON)**2
                    min_idx = dist.argmin()
                    # Unravel index
                    y_idx, x_idx = np.unravel_index(min_idx, lats.shape)
                    
                    # Get dimension names (usually y, x or similar)
                    dims = ds['latitude'].dims
                    # Cast to native python int
                    ds_point = ds.isel({dims[0]: int(y_idx), dims[1]: int(x_idx)})
                else:
                     print(f"Skipping {store_name}: coordinate shape mismatch")
                     continue
            else:
                print(f"Skipping {store_name}: No lat/lon coords")
                continue
            
            # Extract steps/time
            steps = ds_point['step'].values
            
            # Handle Step Type (timedelta vs int)
            if np.issubdtype(steps.dtype, np.timedelta64):
                # Convert nanoseconds to hours
                steps_hours = (steps / np.timedelta64(1, 'h')).astype(float)
            else:
                steps_hours = steps.astype(float)

            # Reconstruct time array
            # We assume f000, f001, etc. maps to hourly steps from base
            # If 'time' exists and is array, use it. If scalar, add step.
            times = []
            if 'time' in ds_point.coords:
                t_val = ds_point['time'].values
                # Check if t_val is 0-d array (scalar)
                if t_val.ndim == 0:
                     # Scalar base time
                     tick = pd.to_datetime(t_val.item()) # .item() to get scalar
                     times = [tick + timedelta(hours=int(s)) for s in steps_hours]
                else:
                     # Array of times
                     times = pd.to_datetime(t_val)
            else:
                # Fallback to hardcoded base
                times = [base_dt + timedelta(hours=int(s)) for s in steps_hours]
            
            # Iterate variables
            for var_name in ds_point.data_vars:
                da = ds_point[var_name]
                
                # Check for extra dims (levels)
                extra_dims = [d for d in da.dims if d not in ['step', 'time', 'latitude', 'longitude']]
                
                if not extra_dims:
                    # Single level
                    vals = da.values
                    for i, val in enumerate(vals):
                        all_data.append({
                            'Time': times[i],
                            'Step': steps[i],
                            'Bundle': bundle,
                            'Variable': var_name,
                            'Level_Type': 'surface/single',
                            'Level_Value': 'N/A',
                            'Value': float(val)
                        })
                else:
                    # Multi level (handle 1 extra dim for now, usually enough)
                    dim_name = extra_dims[0]
                    levels = da[dim_name].values
                    
                    # Iterate levels
                    for lvl_idx, lvl_val in enumerate(levels):
                        # Slice data at this level
                        # Handle if da has shape (step, level) or (level, step)?
                        # xarray sel/isel handles dimension order
                        da_level = da.isel({dim_name: lvl_idx})
                        vals = da_level.values
                        
                        for i, val in enumerate(vals):
                            all_data.append({
                                'Time': times[i],
                                'Step': steps[i],
                                'Bundle': bundle,
                                'Variable': var_name,
                                'Level_Type': dim_name,
                                'Level_Value': float(lvl_val),
                                'Value': float(val)
                            })
            
            ds.close()
            print(f"Processed {store_name}: {len(ds_point.data_vars)} variables")
            
        except Exception as e:
            print(f"Error processing {store_name}: {e}")
    
    # Convert to DataFrame
    df = pd.DataFrame(all_data)
    
    # Sort
    df = df.sort_values(by=['Time', 'Bundle', 'Variable'])
    
    # Save
    print(f"\nSaving {len(df)} rows to {output_csv}...")
    df.to_csv(output_csv, index=False)
    print("Done.")
    
    # Verification Summary
    print("\n=== Verification Summary ===")
    print(f"Unique Bundles: {df['Bundle'].unique()}")
    print(f"Unique Variables: {df['Variable'].unique()}")
    print(f"Time Range: {df['Time'].min()} to {df['Time'].max()}")
    print(f"Total Steps: {df['Step'].nunique()}")

if __name__ == "__main__":
    extract_jakarta_data()
