# Benchmark: NetCDF vs Zarr vs Raw Binary

## Executive Summary
For the specific use case of **Time Series Extraction** (fetching history for a single location) and **Random Access**:
- **Consolidated NetCDF**: Good for simple archiving, but slow for time series (4.76s).
- **Consolidated Zarr**: Excellent balance of speed (1.33s), compression (82% smaller), and metadata support.
- **Raw Binary (Math/Byte Seeking)**: The absolute fastest (0.0003s), ~4000x faster than Zarr, but uncompressed and lacks metadata.

### Master Comparison Table
| Metric | NetCDF (Separate) | Consolidated Zarr | Raw Binary (Memmap/Seek) |
|---|---|---|---|
| **Storage Size** (Full Dataset) | ~175 MB (100%) | **~30 MB (16%)** | ~175 MB (Uncompressed)* |
| **Read Speed** (Single Value) | ~0.0033s | ~0.0023s | **0.0003s** (0.3ms) |
| **Time Series Extraction** (139 pts) | 4.76s | 1.33s | **0.0005s** |
| **Coordinate Lookup** | Slow (0.10s) | Fast (0.02s) | **N/A** (Requires external index) |
| **Write Speed** (Throughput) | **~2185 MB/s** | ~557 MB/s | ~600 MB/s (Est) |
| **Concurrency** (500MB RAM) | **12,600 files** | 5,200 stores | Unlimited (OS file handles) |
| **Memory Usage** (Single Read) | ~0.38 MiB | ~0.00 MiB | **0.00 MiB** |
| **Memory Usage** (Full Load) | ~40 MiB | **~10 MiB** | ~715 MiB (Pure Array) |

*\*Note: Raw Binary size estimated based on uncompressed float32 array. Zarr uses compression.*

## Detailed Results

### Size
- **NetCDF**: 183,415,667 bytes (~175 MB)
- **Zarr**: 31,899,489 bytes (~30 MB)
- **Result**: Zarr is approximately **82% smaller** than NetCDF in this test.

## Speed (Read)
Time to open and read a variable from the dataset (10 files/stores):
- **NetCDF**: 0.1299 seconds 
- **Zarr**: 0.0833 seconds
- **Result**: Zarr is approximately **35% faster** to read.

## Spatial Access (Jakarta Coordinate)
Target: Jakarta (-6.2088, 106.8456)
Index found: 142787

### Coordinate Lookup Speed (Reading Lat/Lon arrays)
- **NetCDF**: 0.1024 seconds
- **Zarr**: 0.0227 seconds
- **Result**: Zarr is **4.5x faster** at reading coordinates to find the index.

### Single Value Access Speed (Hot Access)
Average time to read one value at the specific index across files:
- **NetCDF**: ~0.0033 seconds per file
- **Zarr**: ~0.0023 seconds per file
- **Result**: Zarr is **~40% faster** at accessing a single value.

## Resource Usage (RAM)
Peak memory increment during operations:

### Full Variable Load
Simulating loading one full 2D/3D variable into memory:
- **NetCDF**: ~39.75 MiB
- **Zarr**: ~10.48 MiB
- **Result**: Zarr uses **~4x less memory** for this operation. 

### Spatial Access (Single Value)
Simulating opening and reading a single value:
- **NetCDF**: ~0.38 MiB
- **Zarr**: ~0.00 MiB (Negligible increase)
- **Result**: Zarr is extremely efficient for partial reads, incurring almost no memory overhead.

## IO Throughput (Synthetic ~100MB Dataset)
Measured using a synthetic contiguous dataset to isolate I/O performance.

### Write Speed
- **NetCDF**: ~2185 MB/s
- **Zarr**: ~557 MB/s
- **Result**: **NetCDF** is significantly faster at writing (approx 4x). This is likely because writing a single large file is improved by OS caching and has less filesystem metadata overhead than Zarr's multiple chunk files/directories.

### Read Speed
- **NetCDF**: ~780 MB/s
- **Zarr**: ~941 MB/s
- **Result**: **Zarr** is faster at reading (approx 20% faster).

## Concurrency (Max Open Datasets in 500MB RAM)
Simulating opening multiple datasets simultaneously until memory limit (500MB) is reached.
- **NetCDF**: 12,600 datasets
- **Zarr**: 5,200 datasets
- **Result**: **NetCDF** allows >2x more concurrently open datasets within strict memory limits. This is likely because the in-memory metadata overhead for an open Zarr store (which may cache keys/chunks) is higher than a file handle and basic header parse for NetCDF (especially with `decode_cf=False`).

## Parallel Opening Stability (Threading)
Attempting to open 1000 datasets using 16 threads:
- **NetCDF**: Failed (Segmentation Fault). The underlying HDF5 library is not thread-safe for parallel opening without careful locking or serial execution.
- **Zarr**: Requires `dask` for thread-safe chunk management in this context. 

## Time Series Extraction (139 Files, 1 Coordinate)
Extracting separate values for Jakarta across 139 time steps.
- **NetCDF (MFDataset)**: Opening 139 separate files lazily.
  - Time: **3.66s**
- **Consolidated Zarr**: Single Zarr store with 139 time steps (concatenated).
  - Time: **1.23s**
- **Result**: Consolidated **Zarr is ~3x faster**. Accessing 139 separate files incurs significant overhead.

### Specific 'tp' (Total Precipitation) Benchmark
Extracting the 'tp' variable specifically (simulating user query for rainfall history):
- **NetCDF (139 Files)**: 4.76s
- **Consolidated Zarr**: 1.33s
- **Raw Binary (NumPy Memmap)**: 0.0005s
- **Raw Binary (Math/Byte Seeking)**: 0.0003s
- **Result**: Raw Binary is **~2600-4000x faster** than Zarr for hot access to specific time series.

**Note on Raw Binary**: This speed comes at the cost of:
1.  **Size**: Uncompressed (362MB for just 'tp' vs ~30MB for Zarr compressed).
2.  **Usability**: No metadata (units, coords) must be managed separately.
3.  **Flexibility**: Harder to slice by coordinate values (lat/lon) without external index lookup.

## Final Conclusion
For this GRIB2 dataset and typical weather data access patterns:

1.  **Read Performance (Speed & Spatial)**: **Zarr** is the clear winner, faster in both sequential and random access.
2.  **Storage Efficiency**: **Zarr** is significantly more compressed/efficient (82% smaller).
3.  **Memory Efficiency (Operations)**: **Zarr** is much lighter on RAM for actual data operations (read/load).
4.  **Write Performance**: **NetCDF** is faster to write.
5.  **Concurrency (Open Handles)**: **NetCDF** allows more simultaneously open dataset objects per GB of RAM.
6.  **Time Series Access**: **Consolidated Zarr** is 3x faster than reading from separate NetCDF files.

**Recommendation**: 
- Use **NetCDF** if you need to perform high-frequency writing or need to keep tens of thousands of files "open" simultaneously in a memory-constrained environment.
- Use **Zarr** for almost all other cases: analysis, cloud storage, and reading/serving data, due to superior speed, size efficiency, and time-series performance when consolidated.