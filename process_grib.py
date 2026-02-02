import cfgrib
import xarray as xr
import os
import json
import numpy as np
import glob
from PIL import Image

# Batch Processing Configuration
INPUT_DIR = "grib_139_steps"
OUTPUT_DIR = "output"

def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def process_all_files():
    # 1. Find and Sort Files
    pattern = os.path.join(INPUT_DIR, "*.grib2")
    files = glob.glob(pattern)
    
    # Sort by forecast hour in filename (f000, f001, etc.)
    def get_forecast_hour(fname):
        try:
            part = fname.split(".f")[1] # 000m00.grib2
            hour = int(part[0:3])
            return hour
        except:
            return 999
            
    files.sort(key=get_forecast_hour)
    
    print(f"Found {len(files)} files. Starting batch processing...")
    
    frames_meta = []
    grid_meta = None
    
    for i, file_path in enumerate(files):
        print(f"[{i+1}/{len(files)}] Processing {os.path.basename(file_path)}...")
        
        try:
            # Fix for multiple keys (stepType conflict)
            try:
                ds = cfgrib.open_dataset(file_path, backend_kwargs={'filter_by_keys': {'stepType': 'accum'}})
            except:
                try:
                    ds = cfgrib.open_dataset(file_path, backend_kwargs={'filter_by_keys': {'stepType': 'instant'}})
                except:
                    # Last resort
                    ds = cfgrib.open_dataset(file_path)
            
            # Find Variable
            var_name = None
            
            # Priority: Total Precipitation
            if 'tp' in ds.variables:
                var_name = 'tp'
                
            if not var_name:
                for v in ds.variables:
                    if v not in ['latitude', 'longitude', 'time', 'step', 'valid_time', 'surface']:
                        var_name = v
                        break
            
            if not var_name:
                var_name = list(ds.data_vars)[-1]
            
            data = ds[var_name]
            values = data.values
            
            # Extract Grid (Only once)
            if grid_meta is None:
                lats = ds['latitude'].values.flatten()
                lons = ds['longitude'].values.flatten()
                
                # Force Unique for Rectilinear Metadata
                # GRIB data is usually Top-Down (North to South), so Lats should be Descending
                unique_lats = sorted(np.unique(lats).tolist(), reverse=True)
                unique_lons = sorted(np.unique(lons).tolist())
                
                print(f"Grid detected: {len(unique_lats)} Lats x {len(unique_lons)} Lons")
                
                grid_meta = {
                    "type": "rectilinear",
                    "width": len(unique_lons),
                    "height": len(unique_lats),
                    "lats": unique_lats,
                    "lons": unique_lons
                }

            # Normalize Frame
            values = np.nan_to_num(values, nan=0.0)
            
            # CRITICAL: Reshape to 2D (Height, Width) to ensure image is not 1D strip
            if grid_meta and 'height' in grid_meta and 'width' in grid_meta:
                try:
                    values = values.reshape((grid_meta['height'], grid_meta['width']))
                    # Fix Orientation: Flip UD if data vs map is inverted
                    values = np.flipud(values) 
                except Exception as e:
                    print(f"Reshape warning: {e}. Keeping original shape.")

            max_val = float(np.max(values))
            min_val = float(np.min(values))
            
            scale_range = max_val - min_val
            if scale_range == 0: scale_range = 1
            
            img_data = ((values - min_val) / scale_range * 255.0).astype(np.uint8)
            
            # Save WebP (Lossless)
            img = Image.fromarray(img_data, mode='L')
            fname_out = f"weather_{i}.webp"
            output_path = os.path.join(OUTPUT_DIR, fname_out)
            img.save(output_path, format='WEBP', lossless=True, quality=100)
            
            frames_meta.append({
                "index": i,
                "file": fname_out,
                "min": min_val,
                "max": max_val,
                "hour": get_forecast_hour(file_path)
            })
            
            ds.close()
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue

    # Save Manifest
    manifest = {
        "grid": grid_meta,
        "frames": frames_meta
    }
    
    with open(os.path.join(OUTPUT_DIR, "manifest.json"), "w") as f:
        json.dump(manifest, f)
        
    print("Batch processing complete.")
    manifest_size = os.path.getsize(os.path.join(OUTPUT_DIR, "manifest.json"))
    print(f"Manifest Size: {manifest_size} bytes")

if __name__ == "__main__":
    ensure_output_dir()
    process_all_files()
