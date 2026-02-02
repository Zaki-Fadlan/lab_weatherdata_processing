import cfgrib
import glob
import os
import xarray as xr

def inspect_dimensions():
    input_dir = "grib_files"
    files = sorted(glob.glob(os.path.join(input_dir, "*.grib2")))
    if not files:
        print("No files found.")
        return

    f = files[0]
    print(f"Inspecting dimensions in {os.path.basename(f)}...\n")
    
    # We use open_datasets to get the full view
    datasets = cfgrib.open_datasets(f)
    
    found_hidden = False
    
    for i, ds in enumerate(datasets):
        for var_name in ds.data_vars:
            var = ds[var_name]
            
            # Check for coordinates that are not lat/lon/step/time
            coords_of_interest = [c for c in var.coords if c not in ['latitude', 'longitude', 'step', 'time', 'valid_time', 'd'] # d is sometimes a dim
                                  and c in var.dims] # only look at dimensions
            
            # If the variable has extra dimensions, print them
            if coords_of_interest:
                print(f"Variable: {var_name}")
                for coord in coords_of_interest:
                    vals = ds[coord].values
                    if vals.size > 1:
                        print(f"  Dimension '{coord}' has {vals.size} levels: {vals}")
                        found_hidden = True
                    else:
                        print(f"  Dimension '{coord}' matched but single level: {vals}")
    
    if not found_hidden:
        print("\nNo other multi-level (hidden) data found.")
    else:
        print("\n^ Above variables contain multiple levels/dimensions.")

if __name__ == "__main__":
    inspect_dimensions()
