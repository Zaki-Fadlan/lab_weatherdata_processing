import cfgrib
import glob
import os

def check_uv_levels():
    files = sorted(glob.glob(os.path.join("grib_files", "*.grib2")))
    if not files:
        return
    
    f = files[0]
    print(f"Checking levels for u, v in {f}...")
    
    # Filter for heightAboveGround
    filter_keys = {'typeOfLevel': 'heightAboveGround', 'stepType': 'instant'}
    
    try:
        ds = cfgrib.open_dataset(f, backend_kwargs={'filter_by_keys': filter_keys})
        
        if 'heightAboveGround' in ds.coords:
            levels = ds.coords['heightAboveGround'].values
            print(f"Found levels for heightAboveGround: {levels}")
            
            # Check variables that depend on this
            print("Variables using heightAboveGround:")
            for var in ds.data_vars:
                if 'heightAboveGround' in ds[var].dims:
                    print(f"  {var}")
        else:
            print("No heightAboveGround coordinate found!")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_uv_levels()
