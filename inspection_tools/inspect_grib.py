import cfgrib
import xarray as xr
import sys
import os

FILE = "grib_139_steps/srfs.20260131.t12z.03km.core-v2.equatorial-southeast-asia.f000m00.grib2"

def inspect():
    print(f"Inspecting {FILE}...")
    
    # 1. Try default open
    print("\n--- TEST 1: Default Open ---")
    try:
        ds = cfgrib.open_dataset(FILE)
        print("Variables:", list(ds.data_vars))
        for v in ds.data_vars:
            print(f"  {v}: {ds[v].dims} {ds[v].shape}")
    except Exception as e:
        print(f"Error: {e}")

    # 2. Try 'instant'
    print("\n--- TEST 2: stepType='instant' ---")
    try:
        ds = cfgrib.open_dataset(FILE, backend_kwargs={'filter_by_keys': {'stepType': 'instant'}})
        print("Variables:", list(ds.data_vars))
        for v in ds.data_vars:
            print(f"  {v}: {ds[v].dims} {ds[v].shape}")
            if 'u' in v.lower() or 'v' in v.lower():
               print(f"     -> details: {ds[v]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect()
