# hotspot - Generating Maps of Land Surface Temperature (LST) and Urban Index (UI) from Copernicus Sentinel Data

This project aims to generate maps of Land Surface Temperature (LST) and Urban Index (UI) using data from the Copernicus Sentinel satellites. It leverages Sentinel-2 and Sentinel-3 data to calculate these indexes, which are crucial for urban heat island studies and environmental monitoring.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Downloading Data](#downloading-data)
  - [Calculating Urban Index (UI)](#calculating-urban-index-ui)
  - [Calculating Land Surface Temperature (LST)](#calculating-land-surface-temperature-lst)
- [References](#references)
  - [Land Surface Temperature (LST)](#land-surface-temperature-lst)
  - [Urban Index (UI)](#urban-index-ui)
- [License](#license)

---

## Overview

The `hotspot` application provides tools for:

- **Downloading Sentinel-2 and Sentinel-3 data** for a specified bounding box and date range.
- **Calculating the Urban Index (UI)** to identify urban areas.
- **Calculating Land Surface Temperature (LST)** using empirical models.

These tools are particularly useful for researchers and urban planners interested in analyzing urban heat islands and monitoring environmental changes.

## Features

- **Interactive GUI**: A user-friendly interface built with Tkinter, featuring an integrated map for selecting areas of interest.
- **Bounding Box Selection**: Select bounding boxes directly from the map or input coordinates manually.
- **Data Download**: Download high-resolution Sentinel-2 data and low-resolution Sentinel-3 data for LST calculation.
- **Urban Index Calculation**: Identify urban areas using NDWI, MNDWI, and UI indexes.
- **Land Surface Temperature Calculation**: Compute LST using empirical models based on NIR/SWIR data.

## Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/supermarche/hotspot
   cd hotspot
   ```

2. **Create a Virtual Environment** (optional but recommended):

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**:

   ```bash
   pip install -r src/requirements.txt
   ```

   Ensure that you have all the necessary libraries, including `rasterio`, `pyproj`, `numpy`, `tkinter`, and others.


4. **Run Pytest**:

    To ensure everything is working correctly, run the tests using `pytest`.

   **Install pytest** (if not already installed):

      ```bash
      pip install pytest
      ```

   **Run the tests**:

      From the root directory of the project, run:

      ```bash
      pytest tests/
      ```

This command will discover and execute all tests located in the `tests` directory, verifying that the functionality is working as expected.

## Usage

Run the application:

```bash
python src/gui_python.py
```

### Downloading Data

1. **Select Bounding Box**:
   - Use the integrated map to zoom to your area of interest.
   - You can search for a city using the "Search City" function.
   - Click "Update BBox from Map" to set the bounding box based on the current map view.

2. **Set Parameters**:
   - **CRS (EPSG code)**: Coordinate Reference System for the bounding box (e.g., `32633` for UTM zone 33N).
   - **Start Date** and **End Date**: Define the date range for the data.
   - **Filter**: Set filters like `'eo:cloud_cover < 30'` to limit results based on cloud cover.

3. **Select Output Directory**:
   - Click "Browse" to choose where downloaded data will be saved.

4. **Download Data**:
   - Click "Download S2 & S3 Data (LST)" to download data needed for LST calculations.
   - Click "Download S2 Weekly (UI)" to download weekly Sentinel-2 data for UI calculations.

### Calculating Urban Index (UI)

The Urban Index (UI) is calculated to identify urban areas by using spectral characteristics from Sentinel-2 data.

1. **Navigate to the "Calculate UI" Tab**.

2. **Understand the Method**:
   - The method identifies and masks water bodies using the **Normalized Difference Water Index (NDWI)** and the **Modified NDWI (MNDWI)**.
   - It then calculates the **Urban Index (UI)** to detect urban areas and aggregates the results.

3. **Set Parameters**:
   - **NDWI Threshold**: Default is `0.3`. Adjust to refine water masking.
   - **MNDWI Threshold**: Default is `0.3`. Adjust to improve water detection.
   - **Aggregation Method**: Choose from `average`, `median`, `max`, `min` for aggregating multiple images.

4. **Calculate UI**:
   - Click "Calculate UI" to start the computation.
   - The output raster will be saved in the output directory.

**Note**: This is an alpha version; water may still be misidentified as roofs or other urban structures.

#### Indexes Used

- **NDWI (Normalized Difference Water Index)**:
  - **Purpose**: Enhances water features and suppresses vegetation and soil noise.
  - **Calculation**: `NDWI = (Green - NIR) / (Green + NIR)`

- **MNDWI (Modified Normalized Difference Water Index)**:
  - **Purpose**: Improves water detection by reducing urban area interference.
  - **Calculation**: `MNDWI = (Green - SWIR) / (Green + SWIR)`

- **UI (Urban Index)**:
  - **Purpose**: Distinguishes urban areas from other land covers.
  - **Calculation**: `UI = (SWIR - NIR) / (SWIR + NIR)`

### Calculating Land Surface Temperature (LST)

1. **Navigate to the "Calculate LST" Tab**.

2. **Understand the Method**:
   - The LST is calculated using empirical models based on NIR/SWIR data from Sentinel-2 and thermal data from Sentinel-3.

3. **Calculate LST**:
   - Click "Calculate LST" to start the computation.
   - The process may take some time, depending on the size of the data and computational resources.
   - The output raster will be saved in the output directory.

**Note**: This feature is in alpha version and may not work as expected.

---

## References

### Land Surface Temperature (LST)

- **Low-Resolution Products**:
  - Copernicus Level 2 LST products are available but not suitable for detailed urban area heat classification.
    - [Copernicus Land Surface Temperature](https://docs.sentinel-hub.com/api/latest/data/planet/planetary-variables/land-surface-temp/)
    - [Sentinel-3 SLSTR Level 2 LST](https://sentinels.copernicus.eu/web/sentinel/technical-guides/sentinel-3-slstr/level-2/land-surface-temperature-lst)

- **Empirical Models with Sentinel-2**:
  - Empirical models based on NIR/SWIR data provide higher resolution LST estimations suitable for urban studies.
    - [SEN4LST Algorithm](https://www.brockmann-consult.de/mvn/os/org/esa/beam/sen4lst/)
    - **References**:
      - Sobri et al., "s6_2sobri.pdf"
      - "Land_Surface_Temperature_Retrieval_from_Landsat_5.pdf"

- **Case Studies and Examples**:
  - [Urban Heat Island Mapping with Sentinel-2 and Sentinel-3](https://terrascope.be/en/cases/urban-heat-island-mapping-combined-sentinel-2-and-sentinel-3-observations)
  - **Landsat Example**:
    - [Land Surface Temperature Mapping with Landsat 8](https://custom-scripts.sentinel-hub.com/landsat-8/land_surface_temperature_mapping/)
  - **Sentinel-3 Example**:
    - [Land Surface Temperature with Sentinel-3](https://custom-scripts.sentinel-hub.com/sentinel-3/land_surface_temperature/)
  - **Overview of LST in Remote Sensing**:
    - "520257208.pdf"

### Urban Index (UI)

- **Urban Index Overview**:
  - The Urban Index is a spectral index used to identify urban areas based on satellite imagery.
  - It utilizes the reflectance characteristics of urban materials, which differ from vegetation and water bodies.

- **Calculations and Methodology**:
  - **NDWI** and **MNDWI** are used to mask water bodies to prevent misclassification.
  - **UI** is then calculated to highlight urban features.
  - Aggregation methods help in combining multiple images to reduce noise and improve accuracy.

- **References**:
  - Zha, Y., Gao, J., & Ni, S. (2003). **Use of normalized difference built-up index in automatically mapping urban areas from TM imagery**. International Journal of Remote Sensing, 24(3), 583-594.
  - Xu, H. (2007). **Extraction of urban built-up land features from Landsat imagery using a thematic-oriented index combination technique**. Photogrammetric Engineering & Remote Sensing, 73(12), 1381-1391.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Disclaimer**: The tools provided are in the alpha version and may not produce fully accurate results. The methods used involve complex calculations that can be influenced by atmospheric conditions, sensor calibration, and other factors. Users are advised to validate the outputs against ground truth data when possible.

---

Feel free to contribute to this project by submitting issues or pull requests. Your feedback is valuable for improving the accuracy and usability of these tools.

---

**Contact**: For questions or support, please contact [your_email@example.com](mailto:your_email@example.com).