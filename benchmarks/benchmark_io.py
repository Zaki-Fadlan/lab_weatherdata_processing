import xarray as xr
import numpy as np
import time
import os
import shutil

# Create a synthetic dataset
# Size ~ 100MB to be significant enough
# 500 x 500 x 50 floats (8 bytes) = 12,500,000 * 8 = 100 MB
dims = ('time', 'x', 'y')
shape = (50, 500, 500)
data = np.random.rand(*shape).astype(np.float64)

ds = xr.Dataset(
    {"temperature": (dims, data)},
    coords={
        "time": np.arange(50),
        "x": np.arange(500),
        "y": np.arange(500),
    }
)

def benchmark_write(ds, path, engine):
    if os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
            
    start = time.time()
    if engine == 'netcdf4':
        ds.to_netcdf(path, engine=engine)
    elif engine == 'zarr':
        ds.to_zarr(path, mode='w')
    end = time.time()
    
    size = 0
    if os.path.isfile(path):
        size = os.path.getsize(path)
    else:
        # Directory size for Zarr
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                size += os.path.getsize(fp)
                
    return end - start, size

def benchmark_read(path, engine):
    start = time.time()
    kwargs = {'engine': engine}
    if engine == 'netcdf4':
         kwargs['decode_cf'] = False
         
    with xr.open_dataset(path, **kwargs) as ds_read:
        # Force read of data
        _ = ds_read['temperature'].values
    end = time.time()
    return end - start

if __name__ == "__main__":
    print("Benchmarking IO Throughput (Synthetic ~100MB Dataset)...")
    
    # Paths
    nc_path = "benchmark_io_test.nc"
    zarr_path = "benchmark_io_test.zarr"
    
    # Write Test
    print("\n--- Write Speed ---")
    t_write_nc, size_nc = benchmark_write(ds, nc_path, 'netcdf4')
    mb_nc = size_nc / (1024 * 1024)
    print(f"NetCDF: Wrote {mb_nc:.2f} MB in {t_write_nc:.4f}s ({mb_nc/t_write_nc:.2f} MB/s)")
    
    t_write_zarr, size_zarr = benchmark_write(ds, zarr_path, 'zarr')
    mb_zarr = size_zarr / (1024 * 1024)
    print(f"Zarr:   Wrote {mb_zarr:.2f} MB in {t_write_zarr:.4f}s ({mb_zarr/t_write_zarr:.2f} MB/s)")
    
    # Read Test
    print("\n--- Read Speed ---")
    t_read_nc = benchmark_read(nc_path, 'netcdf4')
    print(f"NetCDF: Read {mb_nc:.2f} MB in {t_read_nc:.4f}s ({mb_nc/t_read_nc:.2f} MB/s)")
    
    t_read_zarr = benchmark_read(zarr_path, 'zarr')
    print(f"Zarr:   Read {mb_zarr:.2f} MB in {t_read_zarr:.4f}s ({mb_zarr/t_read_zarr:.2f} MB/s)")
    
    # Cleanup
    if os.path.exists(nc_path):
        os.remove(nc_path)
    if os.path.exists(zarr_path):
        shutil.rmtree(zarr_path)
