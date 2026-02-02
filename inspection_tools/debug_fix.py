import cfgrib
import glob
import os

def debug_grib():
    files = sorted(glob.glob(os.path.join("grib_files", "*.grib2")))
    if not files:
        print("No files found")
        return

    f = files[0]
    print(f"Inspecting {f}...")
    
    datasets = cfgrib.open_datasets(f)
    print(f"Found {len(datasets)} datasets")
    
    for i, ds in enumerate(datasets):
        print(f"\nDataset {i}:")
        
        # Check first variable for GRIB attributes
        first_var_name = list(ds.data_vars)[0]
        first_var = ds[first_var_name]
        
        print(f"  First variable: {first_var_name}")
        print("  Var attributes:")
        for key in ['GRIB_typeOfLevel', 'GRIB_stepType', 'GRIB_shortName']:
            val = first_var.attrs.get(key, 'MISSING')
            print(f"    {key}: {val}")
        
        # Try to deduce valid filter_keys
        filter_keys = {}
        if 'GRIB_typeOfLevel' in first_var.attrs:
            filter_keys['typeOfLevel'] = first_var.attrs['GRIB_typeOfLevel']
        if 'GRIB_stepType' in first_var.attrs:
            filter_keys['stepType'] = first_var.attrs['GRIB_stepType']
            
        print(f"  Duced filter_keys: {filter_keys}")

if __name__ == "__main__":
    debug_grib()
