import xarray as xr
import glob
import os
import psutil
import time
from memory_profiler import memory_usage

TARGET_LAT = -6.2088
TARGET_LON = 106.8456

def get_nearest_index(lat_array, lon_array, target_lat, target_lon):
    dist = (lat_array - target_lat)**2 + (lon_array - target_lon)**2
    return dist.argmin()

def operation_load_full(file_path, engine, decode_cf=True):
    # Simulate loading the dataset and reading one full variable (simulating full read)
    kwargs = {'engine': engine}
    if engine == 'netcdf4':
         kwargs['decode_cf'] = decode_cf
         
    with xr.open_dataset(file_path, **kwargs) as ds:
        # Load the last variable fully into memory
        var_name = list(ds.data_vars)[-1]
        _ = ds[var_name].load()

def operation_access_spatial(file_path, engine, decode_cf=True, idx=0):
    # Simulate partial access
    kwargs = {'engine': engine}
    if engine == 'netcdf4':
         kwargs['decode_cf'] = decode_cf
         
    with xr.open_dataset(file_path, **kwargs) as ds:
        var_name = list(ds.data_vars)[-1]
        _ = ds[var_name][idx].values

def benchmark_memory(file_paths, engine, mode='full'):
    if not file_paths:
        return []
    
    path = file_paths[0] # Test on just one file for clarity vs average
    
    # Pre-calculate index for spatial test
    idx = 0
    if mode == 'spatial':
         # Just use a dummy index or try to calculate if cheap, but we want to measure operation mem
         # Let's say we use a fixed index or the one from previous test
         idx = 142787
    
    def target():
        if mode == 'full':
            operation_load_full(path, engine, decode_cf=(engine!='netcdf4'))
        else:
            operation_access_spatial(path, engine, decode_cf=(engine!='netcdf4'), idx=idx)
            
    # Measure memory
    # interval=0.01s
    mem_usage = memory_usage(target, interval=0.01, timeout=20)
    return max(mem_usage) - min(mem_usage)

if __name__ == "__main__":
    print("Benchmarking Memory Usage (Peak Increment in MiB)...")
    
    netcdf_files = sorted(glob.glob("grib2netcdf/output/*.nc"))
    zarr_files = sorted(glob.glob("grib2zarr/output/*.zarr"))
    
    # 1. Full Load
    print("\n--- Full Load (One Variable) ---")
    mc_nc = benchmark_memory(netcdf_files, 'netcdf4', mode='full')
    print(f"NetCDF: {mc_nc:.2f} MiB")
    
    mc_zarr = benchmark_memory(zarr_files, 'zarr', mode='full')
    print(f"Zarr:   {mc_zarr:.2f} MiB")
    
    # 2. Spatial Access
    print("\n--- Spatial Access (Single Value) ---")
    mc_nc_s = benchmark_memory(netcdf_files, 'netcdf4', mode='spatial')
    print(f"NetCDF: {mc_nc_s:.2f} MiB")
    
    mc_zarr_s = benchmark_memory(zarr_files, 'zarr', mode='spatial')
    print(f"Zarr:   {mc_zarr_s:.2f} MiB")
