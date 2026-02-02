import xarray as xr
import numpy as np
import os

def verify_locations():
    zarr_path = "zarr_output/dataset_1_heightAboveGround_instant.zarr"
    if not os.path.exists(zarr_path):
        print(f"Error: {zarr_path} not found.")
        return

    print(f"Opening {zarr_path}...")
    ds = xr.open_zarr(zarr_path, consolidated=True)
    
    levels = ds['heightAboveGround'].values
    print(f"Available vertical levels: {levels}")
    
    locations = {
        "Jakarta": (-6.2088, 106.8456),
        "Bandung": (-6.9175, 107.6191),
        "Banda Aceh": (5.5483, 95.3238)
    }
    
    # Load coordinates (assuming 1D arrays for 'latitude' and 'longitude')
    # They might be named 'latitude'/'longitude' or 'lat'/'lon'
    lat_name = 'latitude' if 'latitude' in ds else 'lat'
    lon_name = 'longitude' if 'longitude' in ds else 'lon'
    
    if lat_name not in ds:
        print("Error: Could not find latitude coordinates.")
        return

    print("Loading coordinates...")
    lats = ds[lat_name].values
    lons = ds[lon_name].values
    
    print("\nComparing 80m vs 100m Wind Values (u, v):")
    print("-" * 75)
    print(f"{'Location':<12} | {'Level':<5} | {'U (m/s)':<10} | {'V (m/s)':<10} | {'Total Speed':<10}")
    print("-" * 75)

    # Use first time step
    ds_slice = ds.isel(step=0)
    
    for name, (target_lat, target_lon) in locations.items():
        # Nearest neighbor search in 1D
        # (lat - target)^2 + (lon - target)^2
        dist_sq = (lats - target_lat)**2 + (lons - target_lon)**2
        min_idx = np.argmin(dist_sq)
        
        # Verify distance is reasonable
        actual_lat = lats[min_idx]
        actual_lon = lons[min_idx]
        # Approximate distance in km... roughly
        error_deg = np.sqrt(dist_sq[min_idx])
        
        # Extract values at this index
        # u and v dims are likely (height, values) or (values, height)
        # We need to select the index from the 'values' dim
        point_data = ds_slice.isel(values=min_idx)
        
        u_vals = point_data['u'].values
        v_vals = point_data['v'].values
        
        print(f"{name} (dist {error_deg*111:.1f}km)")
        
        vals_db = []
        for i, lev in enumerate(levels):
            u = u_vals[i]
            v = v_vals[i]
            speed = np.sqrt(u**2 + v**2)
            vals_db.append((u, v, speed))
            print(f"{'':<12} | {int(lev):<5} | {u:<10.3f} | {v:<10.3f} | {speed:<10.3f}")
            
        # Check diff
        if len(vals_db) >= 2:
            u_diff = abs(vals_db[1][0] - vals_db[0][0])
            v_diff = abs(vals_db[1][1] - vals_db[0][1])
            if u_diff > 0.001 or v_diff > 0.001:
                print(f"{'':<12} => DISTINCT VALUES (Diff U={u_diff:.3f}, V={v_diff:.3f})")
            else:
                 print(f"{'':<12} => IDENTICAL VALUES (Warning)")
        print("-" * 75)

if __name__ == "__main__":
    verify_locations()
