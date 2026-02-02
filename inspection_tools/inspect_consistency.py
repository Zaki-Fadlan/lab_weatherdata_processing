import cfgrib
import glob
import os
import time

def inspect_all_files():
    input_dir = "grib_files"
    files = sorted(glob.glob(os.path.join(input_dir, "*.grib2")))
    if not files:
        print("No files found.")
        return

    print(f"Found {len(files)} files. Analyzing consistency using open_datasets...")
    
    # Analyze reference (first file)
    ref_file = files[0]
    print(f"Reference file: {os.path.basename(ref_file)}")
    
    def get_file_identifiers(filepath):
        # Returns a set of identifiers for all variables in the file
        # Identifier = (shortName, typeOfLevel, stepType)
        identifiers = set()
        try:
            # open_datasets splits the file into consistent datasets automatically
            datasets = cfgrib.open_datasets(filepath)
            for ds in datasets:
                # helper to get dataset-wide attributes if missing from vars
                ds_level = ds.attrs.get('GRIB_typeOfLevel', 'unknown')
                ds_step = ds.attrs.get('GRIB_stepType', 'unknown')
                
                for var_name in ds.data_vars:
                    # Get specific attributes for the variable
                    attrs = ds[var_name].attrs
                    short_name = attrs.get('GRIB_shortName', var_name)
                    level = attrs.get('GRIB_typeOfLevel', ds_level)
                    step = attrs.get('GRIB_stepType', ds_step)
                    
                    identifiers.add((short_name, level, step))
        except Exception as e:
            print(f"Error reading {os.path.basename(filepath)}: {e}")
            return None # Indicate failure
            
        return identifiers

    print("Scanning reference file...")
    ref_vars = get_file_identifiers(ref_file)
    if ref_vars is None:
        print("Critical: Failed to read reference file!")
        return
        
    print(f"Reference contains {len(ref_vars)} unique variable signatures.")
    for v in sorted(list(ref_vars)):
        print(f"  - {v}")
    
    # Scan others
    new_findings = {}
    failed_files = []
    
    print("\nScanning all files...")
    start_time = time.time()
    
    for i, file in enumerate(files[1:], 1):
        if i % 10 == 0:
            print(f"  Processed {i}/{len(files)-1}...")
            
        current_vars = get_file_identifiers(file)
        
        if current_vars is None:
            failed_files.append(os.path.basename(file))
            continue
            
        # Check for new vars
        diff = current_vars - ref_vars
        if diff:
            fname = os.path.basename(file)
            new_findings[fname] = diff
            print(f"  [!] Found new data in {fname}: {diff}")
            ref_vars.update(diff)
            
    elapsed = time.time() - start_time
    print(f"\nScan complete in {elapsed:.1f}s")
    
    if failed_files:
        print(f"\n[!] WARNING: {len(failed_files)} files failed to open:")
        print(failed_files[:5], "..." if len(failed_files)>5 else "")

    if new_findings:
        print("\n=== NEW HIDDEN DATA FOUND ===")
        for fname, vars_ in new_findings.items():
            print(f"File: {fname}")
            for v in vars_:
                print(f"  + {v}")
    else:
        print("\n=== No hidden data found. all files are consistent. ===")

if __name__ == "__main__":
    inspect_all_files()
