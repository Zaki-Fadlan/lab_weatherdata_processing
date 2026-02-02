import cfgrib
import xarray as xr
import os
import json
import numpy as np
import glob
from PIL import Image
import sys

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
    
    # Sort by forecast hour
    def get_forecast_hour(fname):
        try:
            part = fname.split(".f")[1] 
            hour = int(part[0:3])
            return hour
        except:
            return 999
            
    files.sort(key=get_forecast_hour)
    
    # DEBUG: Processing all files
    print(f"Found {len(files)} files. Starting batch processing...")
    
    frames_meta = []
    grid_meta = None
    
    # Processing Loop
    for i, file_path in enumerate(files):
        print(f"[{i+1}/{len(files)}] Processing {os.path.basename(file_path)}...")
        
        ds = None
        # Try finding wind (10m height)
        try:
            # OPTION 1: Specific 10m height
            ds = cfgrib.open_dataset(file_path, backend_kwargs={'filter_by_keys': {'typeOfLevel': 'heightAboveGround', 'level': 10}})
        except Exception as e1:
            try:
                # OPTION 2: Generic 'instant' (might fail due to mixing levels)
                ds = cfgrib.open_dataset(file_path, backend_kwargs={'filter_by_keys': {'stepType': 'instant'}})
            except Exception as e2:
                 # OPTION 3: Fallback (reads first available)
                 try:
                    ds = cfgrib.open_dataset(file_path)
                 except Exception as e3:
                    print(f"  Failed all open attempts: {e1} | {e2} | {e3}")
                    continue

        # Find U and V Variables (names vary)
        u_name = None
        v_name = None
        
        for v_key in ds.variables:
            k = v_key.lower()
            if k in ['u10', '10u', 'u', 'u-component_of_wind', 'ugrd']: u_name = v_key
            if k in ['v10', '10v', 'v', 'v-component_of_wind', 'vgrd']: v_name = v_key
            
        if not u_name or not v_name:
            # Try searching partial matches
            for v_key in ds.variables:
                if v_key.lower().startswith('u') and not u_name: u_name = v_key
                if v_key.lower().startswith('v') and not v_name: v_name = v_key
        
        if not u_name or not v_name:
            print(f"  Warning: U/V not found in {file_path}. Vars: {list(ds.variables)}")
            ds.close()
            continue

        try:
            u_data = ds[u_name].values
            v_data = ds[v_name].values
            
            # Grid Metadata
            if grid_meta is None:
                lats = ds['latitude'].values.flatten()
                lons = ds['longitude'].values.flatten()
                unique_lats = sorted(np.unique(lats).tolist(), reverse=True)
                unique_lons = sorted(np.unique(lons).tolist())
                print(f"  Grid: {len(unique_lats)}x{len(unique_lons)}")
                grid_meta = {
                    "type": "rectilinear",
                    "width": len(unique_lons),
                    "height": len(unique_lats),
                    "lats": unique_lats,
                    "lons": unique_lons
                }

            # Reshape
            u_data = np.nan_to_num(u_data, nan=0.0)
            v_data = np.nan_to_num(v_data, nan=0.0)
            
            if grid_meta and 'height' in grid_meta and 'width' in grid_meta:
                 u_data = u_data.reshape((grid_meta['height'], grid_meta['width']))
                 v_data = v_data.reshape((grid_meta['height'], grid_meta['width']))
                 # Flip UD: Data is South-to-North (stored S->N), but we need North-at-Top (Image convention)
                 u_data = np.flipud(u_data)
                 v_data = np.flipud(v_data)

            # Normalize
            u_max = float(np.max(u_data))
            u_min = float(np.min(u_data))
            v_max = float(np.max(v_data))
            v_min = float(np.min(v_data))
            
            u_range = u_max - u_min if (u_max - u_min) != 0 else 1
            v_range = v_max - v_min if (v_max - v_min) != 0 else 1
            
            u_img = ((u_data - u_min) / u_range * 255.0).astype(np.uint8)
            v_img = ((v_data - v_min) / v_range * 255.0).astype(np.uint8)
            b_img = np.zeros_like(u_img)
            
            rgb = np.dstack((u_img, v_img, b_img))
            img = Image.fromarray(rgb, mode='RGB')
            # Save WebP (Lossless)
            # Use len(frames_meta) to ensure contiguous indices (0, 1, 2...) even if source files are skipped
            idx_out = len(frames_meta)
            fname = f"wind_{idx_out}.webp"
            img.save(os.path.join(OUTPUT_DIR, fname), format='WEBP', lossless=True)
            
            frames_meta.append({
                "index": idx_out,
                "file": fname,
                "u_min": u_min, "u_max": u_max,
                "v_min": v_min, "v_max": v_max,
                "hour": get_forecast_hour(file_path)
            })
            
        except Exception as e:
            print(f"  Error extracting data: {e}")
            
        ds.close()

    # Save Manifest
    manifest = {"grid": grid_meta, "frames": frames_meta}
    with open(os.path.join(OUTPUT_DIR, "manifest_wind.json"), "w") as f:
        json.dump(manifest, f)
    print("Done. Saved to manifest_wind.json")

if __name__ == "__main__":
    ensure_output_dir()
    process_all_files()
