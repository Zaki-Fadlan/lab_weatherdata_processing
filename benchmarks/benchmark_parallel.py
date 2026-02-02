import xarray as xr
import glob
import time
import concurrent.futures

def open_dataset_safe(path, engine):
    kwargs = {'engine': engine}
    if engine == 'netcdf4':
         kwargs['decode_cf'] = False
    try:
        ds = xr.open_dataset(path, **kwargs)
        return True
    except Exception as e:
        return False

def benchmark_parallel(file_paths, engine, max_workers=16):
    if not file_paths:
        return 0.0, 0
    
    # Duplicate paths to have enough work
    work_items = (file_paths * (1000 // len(file_paths) + 1))[:1000]
    
    start_time = time.time()
    success_count = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(open_dataset_safe, path, engine) for path in work_items]
        for future in concurrent.futures.as_completed(futures):
            if future.result():
                success_count += 1
                
    end_time = time.time()
    return end_time - start_time, success_count

if __name__ == "__main__":
    print("Benchmarking Parallel Open (1000 operations, 16 threads)...")
    
    netcdf_files = sorted(glob.glob("grib2netcdf/output/*.nc"))
    zarr_files = sorted(glob.glob("grib2zarr/output/*.zarr"))
    
    # NetCDF
    print("\n--- NetCDF Parallel Open ---")
    t_nc, count_nc = benchmark_parallel(netcdf_files, 'netcdf4')
    print(f"NetCDF: Opened {count_nc} files in {t_nc:.4f}s ({count_nc/t_nc:.2f} files/sec)")
    
    # Zarr
    print("\n--- Zarr Parallel Open ---")
    t_zarr, count_zarr = benchmark_parallel(zarr_files, 'zarr')
    print(f"Zarr:   Opened {count_zarr} stores in {t_zarr:.4f}s ({count_zarr/t_zarr:.2f} stores/sec)")
