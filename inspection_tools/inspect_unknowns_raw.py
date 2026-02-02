import cfgrib
import glob
import os

def inspect_raw():
    files = sorted(glob.glob(os.path.join("grib_files", "*.grib2")))
    if not files:
        print("No files found")
        return

    f = files[0]
    print(f"Inspecting raw messages in {f}...")
    
    # helper to print keys
    keys = ['name', 'shortName', 'discipline', 'parameterCategory', 'parameterNumber', 'typeOfLevel', 'stepType']
    
    # We use cfgrib.open_file to iterate messages
    with cfgrib.open_file(f) as file:
        count = 0
        for msg in file:
            # We are looking for things that might be unknown or match the missing vars
            # But efficiently.
            
            # Let's just check the ones that have 'unknown' in name or shortName
            try:
                short_name = msg.get('shortName', 'N/A')
                name = msg.get('name', 'N/A')
                
                if short_name == 'unknown' or name == 'unknown':
                    print(f"\nMessage {count}:")
                    for k in keys:
                        val = msg.get(k, 'N/A')
                        print(f"  {k}: {val}")
            except Exception as e:
                print(f"Error reading message {count}: {e}")
            
            count += 1

if __name__ == "__main__":
    inspect_raw()
