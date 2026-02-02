import cfgrib
import glob
import os
import warnings
import logging

# Suppress annoying warnings
warnings.filterwarnings('ignore')
logging.getLogger('cfgrib').setLevel(logging.ERROR)

def inspect_bundles():
    input_dir = "grib_files"
    bundles = ["core-v2", "upper-air", "thunderstorm", "derived"]
    
    print("Inspecting sample files for each bundle type...\n")
    
    for bundle in bundles:
        print(f"=== BUNDLE: {bundle} ===")
        # Find a sample file
        pattern = os.path.join(input_dir, f"*{bundle}*.grib2")
        files = glob.glob(pattern)
        
        if not files:
            print("  No files found for this bundle.")
            print("-" * 50)
            continue
            
        sample_file = files[0]
        print(f"  Sample File: {os.path.basename(sample_file)}")
        
        try:
            # Open datasets to handle mixed content
            datasets = cfgrib.open_datasets(sample_file)
            
            all_vars = set()
            print(f"  Datasets found: {len(datasets)}")
            
            for i, ds in enumerate(datasets):
                # Identify dataset type
                level_type = ds.attrs.get('GRIB_typeOfLevel', 'unknown')
                step_type = ds.attrs.get('GRIB_stepType', 'unknown')
                
                print(f"  Dataset {i}: Level={level_type}, Step={step_type}")
                
                for var_name in ds.data_vars:
                    var = ds[var_name]
                    # Get robust attributes
                    attrs = var.attrs
                    short_name = attrs.get('GRIB_shortName', var_name)
                    name = attrs.get('GRIB_name', 'unknown')
                    units = attrs.get('GRIB_units', '-')
                    
                    # Check for extra dimensions/levels
                    coords_of_interest = [c for c in var.coords if c not in ['latitude', 'longitude', 'step', 'time', 'valid_time'] and c in var.dims]
                    
                    level_info = ""
                    if coords_of_interest:
                        for coord in coords_of_interest:
                            vals = ds[coord].values
                            if vals.size > 1:
                                level_info += f"  [DIM: {coord} ({vals.size} levels): {vals}]"
                            elif vals.size == 1:
                                level_info += f"  [Fixed: {coord}={vals}]"
                    
                    # Store unique signature: name + level_structure
                    sig = (short_name, name, units, level_info)
                    
                    if sig not in all_vars:
                        print(f"    - {short_name:<10} | {name} ({units}){level_info}")
                        all_vars.add(sig)
                        
        except Exception as e:
            print(f"  Error reading file: {e}")
            
        print("-" * 50)

if __name__ == "__main__":
    inspect_bundles()
