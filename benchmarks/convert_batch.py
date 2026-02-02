import xarray as xr
import cfgrib
import glob
import os
import time

def batch_convert():
    grib_files = sorted(glob.glob("grib_files/*.grib2"))
    print(f"Found {len(grib_files)} GRIB2 files.")
    
    # 1. Convert to separate NetCDF files
    print("\n--- Converting to separate NetCDF files (Targeting 'tp') ---")
    start_nc = time.time()
    out_dir = "grib2netcdf/batch_tp_output"
    os.makedirs(out_dir, exist_ok=True)
    
    processed_nc_files = []
    
    count = 0
    for f in grib_files:
        fname = os.path.basename(f).replace(".grib2", ".nc")
        out_path = os.path.join(out_dir, fname)
        
        # If exists, skip? For now, overwrite or check content? 
        # Better safe to overwrite since previous run might have been different var
        # But we changed dir name, so it's empty.
        
        try:
            # We need to find the dataset with 'tp'
            datasets = cfgrib.open_datasets(f)
            target_ds = None
            for ds in datasets:
                if 'tp' in ds.data_vars:
                    target_ds = ds
                    break
            
            if target_ds:
                # Save just the tp dataset
                target_ds.to_netcdf(out_path)
                processed_nc_files.append(out_path)
                count += 1
                if count % 10 == 0:
                    print(f"Converted {count} files to NetCDF...")
            else:
                print(f"Warning: 'tp' not found in {f}")
                
        except Exception as e:
            print(f"Failed to convert {f}: {e}")
            
    print(f"Finished NetCDF conversion in {time.time() - start_nc:.2f}s")
    
    # 2. Create Consolidated Zarr
    print("\n--- Creating Consolidated Zarr (Targeting 'tp') ---")
    start_zarr = time.time()
    os.makedirs("grib2zarr/batch_tp_output", exist_ok=True)
    zarr_out_path = "grib2zarr/batch_tp_output/consolidated.zarr"
    
    if processed_nc_files:
        try:
            # decode_cf=False avoids the 'dtype' encoding error
            # But wait, if we use decode_cf=False, 'tp' might not be recognized as such if renamed?
            # Usually it's fine.
            ds_mf = xr.open_mfdataset(processed_nc_files, engine='netcdf4', combine='nested', concat_dim='step', decode_cf=False)
            
            ds_mf.to_zarr(zarr_out_path, mode='w')
            print(f"Finished Consolidated Zarr creation in {time.time() - start_zarr:.2f}s")
        except Exception as e:
            print(f"Failed to create consolidated Zarr: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    batch_convert()
