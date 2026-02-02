import os
import xarray as xr
import cfgrib

def convert_grib2_to_netcdf(input_path, output_path):
    print(f"Converting {input_path}...")
    try:
        # cfgrib.open_datasets returns a list of xarray Datasets for each compatible group of messages
        datasets = cfgrib.open_datasets(input_path)
        
        if not datasets:
            print("No datasets found in the GRIB2 file.")
            return

        print(f"Found {len(datasets)} dataset(s).")
        
        base, ext = os.path.splitext(output_path)
        
        for i, ds in enumerate(datasets):
            if len(datasets) == 1:
                current_output = output_path
            else:
                # Append an index or type to the filename if multiple datasets exist
                # We can try to guess a suffix from the valid keys or just use an index
                suffix = ""
                # Try to determine a meaningful suffix from dimensions or attributes data vars
                if 'stepType' in ds.coords:
                     suffix += f"_{ds.stepType.values}"
                else:
                     suffix += f"_{i}"
                
                current_output = f"{base}{suffix}{ext}"

            print(f"Saving dataset {i+1}/{len(datasets)} to {current_output}...")
            print(dataset_summary(ds))
            ds.to_netcdf(current_output)
            
        print("Conversion successful!")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

def dataset_summary(ds):
    lines = []
    lines.append(f"Dimensions: {dict(ds.dims)}")
    lines.append(f"Data variables: {list(ds.data_vars)}")
    return "\n".join(lines)

if __name__ == "__main__":
    # Define paths relative to the project root
    input_file = os.path.join("grib_files", "srfs.20260128.t00z.03km.core-v2.equatorial-southeast-asia.f002m00.grib2")
    output_file = os.path.join("grib2netcdf", "output", "srfs.20260128.t00z.03km.core-v2.equatorial-southeast-asia.f002m00.nc")
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file not found at {input_file}")
        exit(1)

    # Ensure output directory exists (redundant if already created, but good practice)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    convert_grib2_to_netcdf(input_file, output_file)
