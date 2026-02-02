import xarray as xr
import numpy as np
import os
import time

def convert_to_raw():
    print("Converting 'tp' data to Raw Binary (NumPy Memmap)...")
    
    # Source: Consolidated Zarr (fastest to read from)
    zarr_path = "grib2zarr/batch_tp_output/consolidated.zarr"
    if not os.path.exists(zarr_path):
        print("Zarr source not found! Run batch conversion first.")
        return

    out_dir = "raw_binary_output"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "tp_consolidated.dat")
    shape_path = os.path.join(out_dir, "shape.npy") # To store shape/dtype info
    
    start = time.time()
    
    # Load Zarr
    ds = xr.open_dataset(zarr_path, engine='zarr', decode_cf=False)
    
    # Get variable
    if 'tp' in ds:
        da = ds['tp']
    else:
        var_name = list(ds.data_vars)[-1]
        da = ds[var_name]
        
    print(f"Data Shape: {da.shape}, Dtype: {da.dtype}")
    
    # Create Memmap file
    # We allocate space on disk
    mode = 'w+'
    fp = np.memmap(out_path, dtype=da.dtype, mode=mode, shape=da.shape)
    
    # Write data
    # Loading entire array into memory might crash if too big (how big is it?)
    # 139 * ~5MB = ~700MB. Should fit in memory easily (if user has >1GB RAM).
    # IF memory is tight, we should iterate. 
    # Let's write in chunks along time dimension to be safe.
    
    # Data Shape seems to be (time, values) because GRIB loading meant flat surface?
    # Or cfgrib opened it as stack?
    # The error says shape is (139, 683553). This is 2D.
    
    chunk_size = 10
    total_time = da.shape[0]
    
    for i in range(0, total_time, chunk_size):
        end = min(i + chunk_size, total_time)
        # print(f"Writing time steps {i} to {end}...")
        # Slice appropriately for 2D
        if da.ndim == 2:
            fp[i:end, :] = da[i:end, :].values
        else:
            fp[i:end, :, :] = da[i:end, :, :].values
        
    # Flush changes to disk
    fp.flush()
    
    # Save shape and meta info separately (Raw binary has no header!)
    np.save(shape_path, {'shape': da.shape, 'dtype': str(da.dtype)})
    
    end = time.time()
    print(f"Finished Raw Binary conversion into {out_path}")
    print(f"Time taken: {end - start:.2f}s")
    print(f"File Size: {os.path.getsize(out_path) / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    convert_to_raw()
