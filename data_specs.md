# Spire Weather Data Specifications

This document outlines the contents of the GRIB2 data bundles processed by the system.

## 1. core-v2 (Surface & Boundary Layer)

Contains primary meteorological variables at the surface and near-surface levels.

### Dimensions
- **Single Level**: Surface (sfc), Mean Sea Level (msl), 2m, 10m, Cloud Layers.
- **Multi-Level**: Winds at 80m and 100m.

### Variables

| Short Name | Name | Units | Level |
| :--- | :--- | :--- | :--- |
| **u** | U component of wind | m/s | **80m, 100m** |
| **v** | V component of wind | m/s | **80m, 100m** |
| **u10** | 10 metre U wind component | m/s | 10m |
| **v10** | 10 metre V wind component | m/s | 10m |
| **windgust** | Wind speed (gust) | m/s | Surface |
| **2t** | 2 metre temperature | K | 2m |
| **2d** | 2 metre dewpoint temperature | K | 2m |
| **2r** | 2 metre relative humidity | % | 2m |
| **sp** | Surface pressure | Pa | Surface |
| **prmsl** | Pressure reduced to MSL | Pa | MSL |
| **tcc** | Total Cloud Cover | % | - |
| **hcc** | High cloud cover | % | High Cloud Layer |
| **mcc** | Medium cloud cover | % | Middle Cloud Layer |
| **lcc** | Low cloud cover | % | Low Cloud Layer |
| **cdca** | Cloud amount | % | Surface |
| **refc** | Max/Composite Radar Reflectivity | dB | - |
| **blh** | Boundary layer height | m | Surface |
| **tp** | Total Precipitation | kg/m² | Surface |
| **total_snowfall** | Total Snowfall (renamed from unknown) | m | Surface |
| **snow_liquid_ratio**| Snow Liquid Ratio (renamed) | - | Surface |
| **crain** | Categorical rain | Code | Surface |
| **cfrzr** | Categorical freezing rain | Code | Surface |
| **cicep** | Categorical ice pellets | Code | Surface |
| **csnow** | Categorical snow | Code | Surface |
| **sdswrf** | Surface downward short-wave radiation | W/m² | Surface |

---

## 2. upper-air (Pressure Levels)

Contains atmospheric profiled data across 8 standard pressure levels.

### Levels (Isobaric)
**[1000, 925, 850, 700, 500, 300, 200, 100] hPa**

### Variables

| Short Name | Name | Units | Description |
| :--- | :--- | :--- | :--- |
| **t** | Temperature | K | Air temperature at pressure level |
| **u** | U component of wind | m/s | Zonal wind speed |
| **v** | V component of wind | m/s | Meridional wind speed |
| **w** | Vertical velocity | Pa/s | Vertical air motion |
| **gh** | Geopotential height | gpm | Height of the pressure surface |
| **r** | Relative humidity | % | Moisture content |
| **absv** | Absolute vorticity | s⁻¹ | Rotation of the fluid |

---

## 3. thunderstorm (Convere & Severe Weather)

indices and parameters related to atmospheric instability and storm potential.

### Dimensions
- **Single Level**: Entire Atmosphere / Surface

### Variables

| Short Name | Name | Units | Description |
| :--- | :--- | :--- | :--- |
| **cape** | Convective Available Potential Energy | J/kg | Energy available to convective updrafts |
| **cin** | Convective Inhibition | J/kg | Energy preventing convection |
| **lftx** | Surface Lifted Index | K | Stability index |
| **hlcy** | Storm Relative Helicity | m²/s² | Potential for rotating updrafts |
| **pwat** | Precipitable water | kg/m² | Total water vapor in column |
| **vucsh** | Vertical u-component shear | s⁻¹ | Wind shear vector (U) |
| **vvcsh** | Vertical v-component shear | s⁻¹ | Wind shear vector (V) |
| **ustm** | U-component storm motion | m/s | Estimated storm movement (U) |
| **vstm** | V-component storm motion | m/s | Estimated storm movement (V) |
| **gh** | Geopotential height | gpm | (Dataset specific level) |

---

## 4. derived (Anomalies)

Derived fields showing deviations from climatological norms or specific layer properties.

### Dimensions
- **Single Level**

### Variables

| Short Name | Name | Units | Description |
| :--- | :--- | :--- | :--- |
| **ta** | Temperature anomaly | K | Deviation from average temperature |
| **gpa** | Geopotential height anomaly | gpm | Deviation from average height |
| **thick** | Thickness | m | Thickness of atmospheric layer |
