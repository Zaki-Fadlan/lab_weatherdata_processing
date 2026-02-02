import cfgrib
import glob
import os

def inspect_unknowns():
    files = sorted(glob.glob(os.path.join("grib_files", "*.grib2")))
    if not files:
        print("No files found")
        return

    f = files[0]
    print(f"Inspecting {f} for 'unknown' variables...")
    
    datasets = cfgrib.open_datasets(f)
    
    found_unknown = False
    for i, ds in enumerate(datasets):
        for var_name in ds.data_vars:
            if 'unknown' in var_name:
                found_unknown = True
                var = ds[var_name]
                print(f"\nDataset {i} - Variable: {var_name}")
                print(f"  Dimensions: {var.dims}")
                print("  Attributes:")
                for k, v in var.attrs.items():
                    if k.startswith('GRIB_') or k in ['long_name', 'units', 'standard_name']:
                        print(f"    {k}: {v}")

    if not found_unknown:
        print("No 'unknown' variables found.")

if __name__ == "__main__":
    inspect_unknowns()
