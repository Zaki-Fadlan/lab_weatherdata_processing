# GRIB Data Processing

This project provides tools to process GRIB2 weather data and convert it into various formats for visualization and analysis.

## Setup

1.  **Environment**: Ensure you are in the Python virtual environment.
    ```powershell
    .\venv\Scripts\Activate.ps1
    ```
2.  **Dependencies**: Install required packages.
    ```powershell
    pip install -r requirements.txt
    ```

## Usage

Run the main processing script:

```powershell
python process_grib.py
```

## Features

-   **GRIB Reader**: Reads all `.grib2` files in `grib_139_steps` directory.
-   **Point Extraction**: Extracts data for specific coordinates (e.g., Jakarta) to CSV/Parquet.
-   **Zarr Export**: Converts the entire dataset to Zarr format (`output/weather_data.zarr`) for efficient cloud analysis.
-   **COG Export**: Converts variables (like Temperature `t2m`, Precipitation `tp`) to Cloud-Optimized GeoTIFF (`output/*.tif`).
