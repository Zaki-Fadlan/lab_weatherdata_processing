import xarray as xr
import glob
import os
import psutil
import time
import sys

# Limit: 500MB in bytes
RAM_LIMIT = 500 * 1024 * 1024

def get_process_memory():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss

def benchmark_concurrency(file_paths, engine):
    if not file_paths:
        return 0
    
    datasets = []
    
    initial_memory = get_process_memory()
    print(f"Initial Memory: {initial_memory / 1024 / 1024:.2f} MB")
    
    try:
        # We cycle through the available files to simulate opening "many" files
        # even if we have to reuse the same paths (simulating different time steps or simple concurrency)
        # Using a generator/loop to keep opening until limit
        
        count = 0
        while True:
            # Pick a file (round robin)
            fpath = file_paths[count % len(file_paths)]
            
            kwargs = {'engine': engine}
            if engine == 'netcdf4':
                 kwargs['decode_cf'] = False # For fair comparison of raw structure overhead
            
            # Open and append to list to keep reference alive (and thus memory)
            ds = xr.open_dataset(fpath, **kwargs)
            datasets.append(ds)
            
            count += 1
            
            if count % 100 == 0:
                current_mem = get_process_memory()
                if current_mem > RAM_LIMIT:
                    print(f"Hit 2GB limit at {count} datasets.")
                    break
                # Optional: print status every 1000
                if count % 1000 == 0:
                    print(f"Opened {count} datasets. Mem: {current_mem / 1024 / 1024:.2f} MB")
                    
            # Safety break to avoid infinite loop if unrelated to memory
            if count > 100000: 
                print("Hit safety limit of 100,000 open datasets.")
                break
                
    except OSError as e:
        print(f"OS Error (likely file limit): {e}")
        # This usually happens at 1024 files on linux ulimit
    except Exception as e:
        print(f"Error: {e}")
        
    final_memory = get_process_memory()
    print(f"Final Memory: {final_memory / 1024 / 1024:.2f} MB")
    
    # Clean up to release memory for next run
    datasets.clear()
    import gc
    gc.collect()
    
    return count

if __name__ == "__main__":
    print(f"Benchmarking Max Concurrent Open Files (Limit: 2GB = {RAM_LIMIT/1024/1024:.2f} MB)...")
    
    netcdf_files = sorted(glob.glob("grib2netcdf/output/*.nc"))
    zarr_files = sorted(glob.glob("grib2zarr/output/*.zarr"))

    if not netcdf_files:
        print("No NetCDF files found.")
    else:
        print("\n--- NetCDF Concurrency ---")
        count_nc = benchmark_concurrency(netcdf_files, 'netcdf4')
        print(f"NetCDF: Could keep {count_nc} datasets open before hitting limits.")

    if not zarr_files:
        print("No Zarr files found.")
    else:
        print("\n--- Zarr Concurrency ---")
        count_zarr = benchmark_concurrency(zarr_files, 'zarr')
        print(f"Zarr:   Could keep {count_zarr} datasets open before hitting limits.")
