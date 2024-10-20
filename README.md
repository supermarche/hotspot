# hotspot - generating maps of the land surface temperature from copernicus / sentinel data

References:
- Land Surface Temperature (LST):
  - As a level 2 product from copernicus, low resolution. Not suitable for urban area heat classification.
    - https://docs.sentinel-hub.com/api/latest/data/planet/planetary-variables/land-surface-temp/
    - https://sentinels.copernicus.eu/en/web/sentinel/technical-guides/sentinel-3-slstr/level-2/land-surface-temperature-lst
  - With empirical models based on NIR/SWIR data from copernicus / sentinel 2.
    - https://www.brockmann-consult.de/mvn/os/org/esa/beam/sen4lst/
    - ref:
      - s6_2sobri.pdf
      - Land_Surface_Temperature_Retrieval_from_Landsat_5.pdf
    - https://terrascope.be/en/cases/urban-heat-island-mapping-combined-sentinel-2-and-sentinel-3-observations
      - LandSat example: https://custom-scripts.sentinel-hub.com/landsat-8/land_surface_temperature_mapping/
      - Sentinel 3 example: https://custom-scripts.sentinel-hub.com/sentinel-3/land_surface_temperature/
  - LST / remote sensing overview: 520257208.pdf
