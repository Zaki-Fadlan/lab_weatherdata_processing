import cfgrib
import numpy as np
import os

FILE = 'grib_139_steps/srfs.20260131.t12z.03km.core-v2.equatorial-southeast-asia.f000m00.grib2'

def inspect():
    print(f"Inspecting {FILE}...")
    ds = None
    try:
        ds = cfgrib.open_dataset(FILE, backend_kwargs={'filter_by_keys': {'stepType': 'instant'}})
    except Exception as e:
        print(f"First attempt failed: {e}. Trying accum...")
        try:
            ds = cfgrib.open_dataset(FILE, backend_kwargs={'filter_by_keys': {'stepType': 'accum'}})
        except Exception as e2:
            print(f"Second attempt failed: {e2}. Trying raw...")
            ds = cfgrib.open_dataset(FILE)

    # Inspect Lats Structure (1D)
    print(f"Latitude Shape: {lats.shape}")
    print(f"Lat[0]: {lats[0]}")
    print(f"Lat[1]: {lats[1]} (Diff: {lats[1]-lats[0]})")
    print(f"Lat[1031]: {lats[1031]} (Assuming Width=1031)")
    
    # Check Row-Major vs Column-Major
    if lats[0] == lats[1]:
        print("Order: Row-Major (Latitude constant along row)")
    else:
        print("Order: Column-Major or Irregular")
        
    print(f"Lat[0] (Start): {lats[0]}")
    print(f"Lat[-1] (End): {lats[-1]}")
    
    # Inspect Data Var
    for v in ds.data_vars:
        if v not in ['latitude', 'longitude', 'time', 'step', 'valid_time', 'surface']:
            data = ds[v].values
            print(f"Variable: {v}")
            print(f"Data Shape: {data.shape}")
            break

if __name__ == "__main__":
    inspect()
