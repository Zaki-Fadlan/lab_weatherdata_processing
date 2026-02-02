import cfgrib
import glob
import os

def inspect_unknowns_filtered():
    files = sorted(glob.glob(os.path.join("grib_files", "*.grib2")))
    if not files:
        print("No files found")
        return

    f = files[0]
    print(f"Inspecting {f} with filters...")

    # We know these combinations from previous runs
    combinations = [
        {'typeOfLevel': 'surface', 'stepType': 'accum'},
        {'typeOfLevel': 'surface', 'stepType': 'instant'},
    ]

    for filter_keys in combinations:
        print(f"\nChecking filter: {filter_keys}")
        try:
            ds = cfgrib.open_dataset(
                f, 
                backend_kwargs={
                    'filter_by_keys': filter_keys,
                    'read_keys': ['discipline', 'parameterCategory', 'parameterNumber', 'typeOfFirstFixedSurface', 'shortName']
                }
            )
            
            for var_name in ds.data_vars:
                # Check if it looks unknown or if it's one of the ones we care about
                # "unknown" often has "unknown" in name or shortName is "unknown"
                var = ds[var_name]
                attrs = var.attrs
                
                is_suspicious = 'unknown' in var_name or attrs.get('GRIB_shortName') == 'unknown'
                
                if is_suspicious:
                    print(f"  [Unknown Variable]: {var_name}")
                    print(f"    Raw Keys:")
                    print(f"      Discipline: {attrs.get('GRIB_discipline', 'N/A')}")
                    print(f"      Category:   {attrs.get('GRIB_parameterCategory', 'N/A')}")
                    print(f"      Number:     {attrs.get('GRIB_parameterNumber', 'N/A')}")
                    print(f"      LevelType:  {attrs.get('GRIB_typeOfLevel', 'N/A')}")
                    print(f"      StepType:   {attrs.get('GRIB_stepType', 'N/A')}")
        except Exception as e:
            print(f"  Failed: {e}")

if __name__ == "__main__":
    inspect_unknowns_filtered()
