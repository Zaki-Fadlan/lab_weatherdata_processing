import numpy as np
import os
import time
from memory_profiler import memory_usage
import psutil

def get_process_memory():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024 # MB

def benchmark_raw_resource():
    print("Benchmarking Raw Binary Resource Usage...")
    
    data_path = "raw_binary_output/tp_consolidated.dat"
    shape_path = "raw_binary_output/shape.npy"
    
    if not os.path.exists(data_path):
        print("Raw data not found.")
        return

    meta = np.load(shape_path, allow_pickle=True).item()
    shape = meta['shape']
    dtype = meta['dtype']
    
    # 1. Measure Open + Seek/Read (Single Value)
    def read_single_value():
        fp = np.memmap(data_path, dtype=dtype, mode='r', shape=shape)
        # Random index
        idx = 142787
        val = fp[0, idx]
        return val

    initial_mem = get_process_memory()
    mem_usage_single = memory_usage(read_single_value, interval=0.01, timeout=5)
    peak_mem_single = max(mem_usage_single) - min(mem_usage_single)
    print(f"Peak Memory (Single Value): {peak_mem_single:.4f} MiB")
    
    # 2. Measure Full Load (Reading one full time step)
    # 683553 floats * 4 bytes = ~2.6 MB. Small.
    # What about full file? 139 * 2.6 = ~360 MB.
    def read_full_file():
        fp = np.memmap(data_path, dtype=dtype, mode='r', shape=shape)
        # Force load into memory
        data = np.array(fp[:]) 
        return data.shape
        
    initial_mem = get_process_memory()
    # This might fail if system is super tight, but we have >500MB likely available for this process alone?
    # The limit was artificial in concurrency script.
    mem_usage_full = memory_usage(read_full_file, interval=0.05, timeout=10)
    peak_mem_full = max(mem_usage_full) - min(mem_usage_full)
    print(f"Peak Memory (Full File Load ~360MB): {peak_mem_full:.4f} MiB")

if __name__ == "__main__":
    benchmark_raw_resource()
