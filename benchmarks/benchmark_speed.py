import xarray as xr
import os
import time
import glob

def benchmark_read(file_paths, engine):
    start_time = time.time()
    count = 0
    for file_path in file_paths:
        # We load the dataset and force computation of something small to ensure it's accessed
        # avoiding lazy loading masquerading as instant load.
        # However, for fair comparison of "opening", we might just do open_dataset.
        # But usually "speed" implies accessing data.
        # Let's read one variable into memory.
        try:
            # Use decode_cf=False to avoid encoding errors during benchmark and measure raw I/O
            kwargs = {'engine': engine}
            if engine == 'netcdf4':
                 kwargs['decode_cf'] = False
            
            with xr.open_dataset(file_path, **kwargs) as ds:
                # Read specific variable names based on what we know, or just the first data var using list
                var_name = list(ds.data_vars)[0]
                _ = ds[var_name].load()
                count += 1
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    end_time = time.time()
    return end_time - start_time, count

if __name__ == "__main__":
    # NetCDF
    netcdf_files = sorted(glob.glob("grib2netcdf/output/*.nc"))
    netcdf_time, nc_count = benchmark_read(netcdf_files, engine="netcdf4")
    print(f"NetCDF: Read {nc_count} files in {netcdf_time:.4f} seconds.")

    # Zarr
    zarr_files = sorted(glob.glob("grib2zarr/output/*.zarr"))
    zarr_time, zarr_count = benchmark_read(zarr_files, engine="zarr")
    print(f"Zarr: Read {zarr_count} stores in {zarr_time:.4f} seconds.")
