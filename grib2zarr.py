import xarray as xr
import cfgrib
import glob
import os
import time
import dask
import contextlib
from dask.distributed import Client, LocalCluster
from dask.diagnostics import ProgressBar
import zarr
import numcodecs
from collections import defaultdict

class Profiler:
    """Profiler to track time and count of steps, plus detailed logs"""
    def __init__(self):
        self.stats = defaultdict(lambda: {'count': 0, 'total_time': 0.0})
        self.details = []
        self.unique_vars = set()
    
    @contextlib.contextmanager
    def step(self, name, extra_info=None):
        start = time.time()
        try:
            yield
        finally:
            elapsed = time.time() - start
            self.stats[name]['count'] += 1
            self.stats[name]['total_time'] += elapsed
            if extra_info:
                info = extra_info.copy()
                info['duration_s'] = elapsed
                self.details.append(info)
                
                # Track unique variables
                if 'variables' in info:
                    # simplistic split, might need refinement if var names contain comma
                    vars_list = [v.strip() for v in info['variables'].split(',')]
                    # Handle renaming lookup if provided
                    if 'renamed' in info:
                        renamed_map = info['renamed']
                        final_vars = []
                        for v in vars_list:
                            final_vars.append(renamed_map.get(v, v))
                        self.unique_vars.update(final_vars)
                    else:
                        self.unique_vars.update(vars_list)
            
    def print_summary(self):
        print("\n" + "="*80)
        print("STEP SUMMARY")
        print(f"{'Step Name':<30} | {'Count':<6} | {'Total (s)':<10} | {'Avg (s)':<10}")
        print("-" * 80)
        for name, data in sorted(self.stats.items(), key=lambda x: x[1]['total_time'], reverse=True):
            avg = data['total_time'] / data['count'] if data['count'] > 0 else 0
            print(f"{name:<30} | {data['count']:<6} | {data['total_time']:<10.2f} | {avg:<10.2f}")
        
        if self.details:
            print("\n" + "="*80)
            print("DETAILED DATASET LOG")
            print("-" * 100)
            for item in self.details:
                vars_str = item.get('variables', 'N/A')
                filter_str = str(item.get('filter', '{}'))
                print(f"Filter: {filter_str}")
                print(f"Time:   {item['duration_s']:.2f}s")
                print(f"Vars:   {vars_str}")
                if 'renamed' in item and item['renamed']:
                    print(f"Renamed: {item['renamed']}")
                if 'levels' in item and item['levels']:
                    print(f"Levels: {item['levels']}")
                print("-" * 100)
        
        # Print total variable count
        print("\n" + "="*80)
        print(f"TOTAL UNIQUE VARIABLES PROCESSED: {len(self.unique_vars)}")
        print(f"List: {sorted(list(self.unique_vars))}")
        print("="*80 + "\n")


profiler = Profiler()

def convert_grib_to_zarr_fast():
    """Ultra-optimized version using Dask distributed scheduler, processing by bundle"""
    with profiler.step("Total Execution"):
        input_dir = "grib_files"
        output_dir = "zarr_output"
        os.makedirs(output_dir, exist_ok=True)
        
        all_files = sorted(glob.glob(os.path.join(input_dir, "*.grib2")))
        if not all_files:
            print(f"No GRIB2 files found in {input_dir}")
            return
        
        # Setup Dask Cluster ONCE
        print("Setting up Dask cluster...")
        cluster = LocalCluster(
            n_workers=4,
            threads_per_worker=2,
            memory_limit='4GB',
            processes=True
        )
        client = Client(cluster)
        print(f"Dask dashboard: {client.dashboard_link}")
        
        try:
            bundles = ['core-v2', 'upper-air', 'thunderstorm', 'derived']
            
            for bundle in bundles:
                print(f"\n{'='*40}")
                print(f"PROCESSING BUNDLE: {bundle}")
                print(f"{'='*40}")
                
                # Filter files for this bundle
                files = [f for f in all_files if bundle in f]
                
                if not files:
                    print(f"No files found for bundle '{bundle}'. Skipping.")
                    continue
                
                print(f"Found {len(files)} files for {bundle}")
                
                # Analyze first file of this bundle to determine structure
                with profiler.step(f"Analyze {bundle}"):
                    print(f"Analyzing structure from: {os.path.basename(files[0])}...")
                    datasets = cfgrib.open_datasets(
                        files[0], 
                        backend_kwargs={'read_keys': ['discipline', 'parameterCategory', 'parameterNumber']}
                    )
                    print(f"Detected {len(datasets)} distinct datasets in {bundle}\n")
                
                for i, ds in enumerate(datasets):
                    filter_keys = {}
                    
                    # Detect variable names
                    short_names = []
                    for var_name in ds.data_vars:
                        sn = ds[var_name].attrs.get('GRIB_shortName')
                        if sn and sn != 'unknown':
                            short_names.append(sn)
                        elif sn == 'unknown':
                             short_names.append('unknown')
                        else:
                            short_names.append(var_name)
                    
                    short_names = sorted(list(set(short_names)))

                    # Helper to check attributes
                    def get_grib_attr(attr_name):
                        if attr_name in ds.attrs: return ds.attrs[attr_name]
                        if ds.data_vars:
                            return ds[list(ds.data_vars)[0]].attrs.get(attr_name)
                        return None

                    type_of_level = get_grib_attr('GRIB_typeOfLevel')
                    step_type = get_grib_attr('GRIB_stepType')
                    
                    if type_of_level: filter_keys['typeOfLevel'] = type_of_level
                    if step_type: filter_keys['stepType'] = step_type
                    
                    if short_names:
                        filter_keys['shortName'] = short_names
                    
                    # Renaming logic
                    rename_map = {}
                    if 'gust' in ds.data_vars:
                        rename_map['gust'] = 'windgust'
                        
                    for var_name in ds.data_vars:
                        if 'unknown' in var_name:
                            attrs = ds[var_name].attrs
                            disc = attrs.get('GRIB_discipline')
                            cat = attrs.get('GRIB_parameterCategory')
                            num = attrs.get('GRIB_parameterNumber')
                            
                            if disc == 0 and cat == 1 and num == 29:
                                rename_map[var_name] = 'total_snowfall'
                            elif disc == 0 and cat == 1 and num == 233:
                                rename_map[var_name] = 'snow_liquid_ratio'

                    uv_levels = []
                    if 'heightAboveGround' in ds.coords:
                         uv_levels = ds['heightAboveGround'].values.tolist()

                    vars_str = ", ".join(ds.data_vars.keys())
                    step_info = {
                        'bundle': bundle,
                        'variables': vars_str,
                        'filter': filter_keys,
                        'renamed': rename_map,
                        'levels': uv_levels
                    }

                    # Construct safe name WITH BUNDLE PREFIX
                    parts = [str(filter_keys.get(k, 'unknown')) for k in ['typeOfLevel', 'stepType']]
                    safe_name = f"{bundle}_dataset_{i}_{parts[0]}_{parts[1]}.zarr"
                    zarr_path = os.path.join(output_dir, safe_name)
                    
                    print(f"Processing {safe_name}...")
                    print(f"  Filter: {filter_keys}")
                    if rename_map: print(f"  Will rename: {rename_map}")
                    
                    with profiler.step(f"Process {safe_name}", extra_info=step_info):
                        try:
                            # Re-using chunks config
                            chunks = {'step': 1, 'latitude': 'auto', 'longitude': 'auto'}
                            
                            with profiler.step("Open mfdataset"):
                                ds_combined = xr.open_mfdataset(
                                    files,
                                    engine='cfgrib',
                                    backend_kwargs={
                                        'filter_by_keys': filter_keys,
                                        'read_keys': ['discipline', 'parameterCategory', 'parameterNumber'],
                                        'indexpath': '',
                                        'errors': 'ignore'
                                    },
                                    combine='nested',
                                    concat_dim='step',
                                    parallel=True,
                                    chunks=chunks,
                                    decode_cf=True, # Ensure CF decoding is ON by default
                                    lock=False,
                                    compat='override',
                                    coords='minimal',
                                    join='override'
                                )
                            
                            # Apply renaming safely
                            if rename_map:
                                safe_rename = {k: v for k, v in rename_map.items() if k in ds_combined}
                                if safe_rename:
                                    ds_combined = ds_combined.rename(safe_rename)
                            
                            # Clean attributes
                            with profiler.step("Clean Attributes"):
                                for coord in ds_combined.coords:
                                    if 'dtype' in ds_combined.coords[coord].attrs:
                                        del ds_combined.coords[coord].attrs['dtype']

                            # Encoding
                            encoding = {}
                            compressor = numcodecs.Blosc(cname='lz4', clevel=3, shuffle=numcodecs.Blosc.SHUFFLE)
                            for var in ds_combined.data_vars:
                                var_chunks = []
                                for dim in ds_combined[var].dims:
                                    if dim in chunks and chunks[dim] != 'auto':
                                        var_chunks.append(chunks[dim])
                                    else:
                                        var_chunks.append(ds_combined.dims[dim])
                                encoding[var] = {'compressor': compressor, 'chunks': tuple(var_chunks)}
                            
                            print(f"  Writing to Zarr...")
                            with profiler.step("Write to Zarr"):
                                with ProgressBar():
                                    ds_combined.to_zarr(
                                        zarr_path, mode='w', encoding=encoding, consolidated=True, compute=True
                                    )
                            ds_combined.close()
                            
                        except Exception as e:
                            print(f"  ✗ Error processing {safe_name}: {e}\n")
                            import traceback
                            traceback.print_exc()

        finally:
            print("Closing Dask cluster...")
            client.close()
            cluster.close()
            profiler.print_summary()
    
    print("\n" + "="*60)
    print("Conversion complete!")
    print(f"Output: {output_dir}")
    print("="*60)

if __name__ == "__main__":
    convert_grib_to_zarr_fast()