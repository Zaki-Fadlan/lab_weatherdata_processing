import xarray as xr
import glob
import os

def inspect_zarr_levels():
    zarr_files = sorted(glob.glob("zarr_output/*.zarr"))
    found_100m = False
    
    print("Inspecting Zarr stores for wind levels...\n")
    
    for zf in zarr_files:
        try:
            ds = xr.open_zarr(zf, consolidated=True)
            subset_vars = [v for v in ds.data_vars if v in ['u', 'v', 'u10', 'v10', '100u', '100v']]
            
            if subset_vars:
                print(f"File: {os.path.basename(zf)}")
                print(f"  Variables: {subset_vars}")
                
                if 'heightAboveGround' in ds.coords:
                    levels = ds['heightAboveGround'].values
                    print(f"  heightAboveGround: {levels}")
                    if 100 in levels:
                        print("  => FOUND 100m LEVEL!")
                        found_100m = True
                else:
                    print("  No heightAboveGround coordinate.")
                print("-" * 40)
                
        except Exception as e:
            print(f"Error opening {zf}: {e}")

    if not found_100m:
        print("\nWARNING: 100m level NOT found in any Zarr store.")
    else:
        print("\nSUCCESS: 100m level found.")

if __name__ == "__main__":
    inspect_zarr_levels()
