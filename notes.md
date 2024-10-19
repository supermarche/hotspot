Hier ist die erweiterte Version der **README.md**, in der auch der Landshut-Satellit sowie die spezifischen Bänder der Satelliten, die in der Software verwendet werden, detailliert beschrieben sind:

---

# City Heatmap Software Documentation

## Introduction
This software utilizes open-source satellite data to create a heatmap for cities, helping urban planners and municipalities to simplify the process of achieving climate goals.

### Key Features:
- Use of Copernicus open-source data (Sentinel-2, Sentinel-3) and Landshut satellite data
- Heatmap creation for city planning and climate goal assessments
- Combination of temperature data with environmental indices to improve accuracy

---

## Data Sources

Three main satellite data sources are utilized:

| **Satellite**   | **Description**                                      | **Use Case**                                       |
|-----------------|------------------------------------------------------|----------------------------------------------------|
| **Sentinel-2**  | High-resolution optical imagery for land monitoring  | Vegetation indices (NDVI), water detection (NDWI)  |
| **Sentinel-3**  | Medium-resolution thermal data for sea/land surfaces | Surface temperature approximation (LST)            |
| **Landshut Satellite** | High-resolution multispectral and thermal bands | Additional temperature and environmental data      |

### Sentinel-2 Bands

Sentinel-2 provides multiple spectral bands. The most relevant for this software are:

| **Band**     | **Description**                    | **Wavelength (nm)** | **Spatial Resolution** |
|--------------|------------------------------------|---------------------|------------------------|
| **B4**       | Red                                | 665                 | 10 m                   |
| **B8**       | Near Infrared (NIR)                | 842                 | 10 m                   |
| **B11**      | Short Wave Infrared (SWIR)         | 1610                | 20 m                   |
| **B12**      | Short Wave Infrared (SWIR)         | 2190                | 20 m                   |

The key bands used for calculating indices are:
- **NDVI**: Uses **B4** (Red) and **B8** (NIR)
- **NBDI**: Uses **B8** (NIR) and **B12** (SWIR)
- **NDWI**: Uses **B4** (Green) and **B8** (NIR)

### Sentinel-3 Bands

Sentinel-3 provides thermal bands that are key to approximating surface temperature. The most relevant bands include:

| **Band**     | **Description**                    | **Wavelength (µm)** | **Spatial Resolution** |
|--------------|------------------------------------|---------------------|------------------------|
| **SLSTR Band 6** | Thermal Infrared (TIR) 1          | 10.85                | 1 km                   |
| **SLSTR Band 7** | Thermal Infrared (TIR) 2          | 12.0                 | 1 km                   |

These thermal bands are critical for calculating the **Land Surface Temperature (LST)** in conjunction with the other environmental indices.

### Landshut Satellite

The Landshut satellite offers high-resolution multispectral and thermal data that complement the Sentinel data. The specific bands include:

| **Band**     | **Description**                    | **Wavelength (µm/nm)** | **Spatial Resolution** |
|--------------|------------------------------------|-------------------------|------------------------|
| **VIS**      | Visible Spectrum (Blue/Green/Red)  | 400-700 nm              | 5 m                    |
| **TIR**      | Thermal Infrared                   | 8-12 µm                 | 100 m                  |

- The **Visible Spectrum** is used to enhance the NDVI calculation for more precise vegetation data.
- The **Thermal Infrared Band (TIR)** from the Landshut satellite provides additional temperature data to improve the LST calculations.

---

## Methodology

1. **Evaluation of Satellite Data**:
    - Initial idea: Use the thermal bands of satellites, but they are too imprecise.
    - Current approach: Combine environmental factors with temperature data for higher accuracy.

2. **Satellite Data Fusion**:
    - **Sentinel-2**: Captures optical imagery useful for environmental indices.
    - **Sentinel-3**: Provides thermal data for surface temperature approximations.
    - **Landshut Satellite**: Adds more high-resolution multispectral and thermal data.

    These datasets are merged to increase the precision of heatmap outputs.

---

## Indices Used

Several key environmental indices are used to enhance the accuracy of the heatmap:

| **Index**       | **Description**                                                                                             | **Formula**                    |
|-----------------|-------------------------------------------------------------------------------------------------------------|--------------------------------|
| **NDVI**        | Normalized Difference Vegetation Index, used to measure vegetation health.                                   | `NDVI = (NIR - Red) / (NIR + Red)` |
| **NBDI**        | Normalized Burn Ratio, used for identifying burnt areas.                                                     | `NBDI = (SWIR - NIR) / (SWIR + NIR)` |
| **NDWI**        | Normalized Difference Water Index, used for water detection in an area.                                      | `NDWI = (Green - NIR) / (Green + NIR)` |

---

## LST (Land Surface Temperature) Approximation

Land Surface Temperature (LST) is calculated by integrating the above indices with **emissivity** (ϵ), which represents surface emissivity, to improve accuracy.

The general formula for LST is:

```
LST = BT / [1 + (λ * BT / ρ) * ln(ϵ)]
```

Where:
- **BT**: Brightness temperature from Sentinel-3
- **λ**: Wavelength of emitted radiance
- **ρ**: Planck’s constant, speed of light, and Boltzmann constant combined
- **ϵ**: Emissivity derived from NDVI or other factors

### Emissivity Calculation (ϵ)

The value of emissivity (ϵ) is calculated based on the surface type:

\[
ϵ = \begin{cases} 
0.975 + 0.005 \cdot NDVI & \text{for vegetated areas (NDVI > 0.2)} \\
0.985 & \text{for water surfaces} \\
0.92 & \text{for bare areas (NDVI ≤ 0.2)} 
\end{cases}
\]

---

## Heatmap Creation Workflow

1. **Collect Satellite Data**:
   - Acquire Sentinel-2 and Landshut data for vegetation, water, and land cover.
   - Acquire Sentinel-3 and Landshut thermal data for surface temperature.

2. **Process Environmental Indices**:
   - Calculate NDVI, NBDI, and NDWI from Sentinel-2 and Landshut data.

3. **Estimate LST**:
   - Use Sentinel-3 and Landshut thermal data combined with the environmental indices and emissivity (ϵ) to calculate the Land Surface Temperature.

4. **Generate Heatmap**:
   - Fuse all data points and generate the heatmap for visual analysis.

---

## Future Work
- Further integration of climate-related datasets such as air quality and pollution levels.
- Enhancement of heatmap resolution by integrating more high-resolution data sources.

---

## Installation & Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-repository/heatmap-software.git
   ```
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the Software**:
   ```bash
   python main.py
   ```

---

Diese erweiterte Version deckt nun den Landshut-Satelliten und seine spezifischen Bänder ab, was die Genauigkeit der Heatmap-Generierung weiter verbessert.