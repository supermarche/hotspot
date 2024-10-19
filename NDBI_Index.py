import rasterio
from rasterio.enums import Resampling
import matplotlib.pyplot as mpyplot
import os
import numpy as np

# Pfad zu deinem .SAFE Ordner
safe_folder = 'S2B_MSIL1C_20241016T100029_N0511_R122_T33UWS_20241016T151956.SAFE/GRANULE/L1C_T33UWS_A039759_20241016T100611/IMG_DATA'

# Lade das Rot-Band (Band 4) und das NIR-Band (Band 8) als .jp2-Dateien
red_band_path = os.path.join(safe_folder, 'T33UWS_20241016T100029_B04.jp2')  # Band 4 (Rot)
nir_band_path = os.path.join(safe_folder, 'T33UWS_20241016T100029_B8A.jp2')  # Band 8A (NIR)
swir_band_path = os.path.join(safe_folder, 'T33UWS_20241016T100029_B11.jp2')  # Band 11 (SWIR)
swir2_band_path = os.path.join(safe_folder, 'T33UWS_20241016T100029_B12.jp2')  # Band 12 (SWIR)

# Zielgröße der Bänder (basierend auf der Größe des Rot-Bandes)
with rasterio.open(red_band_path) as red_src:
    target_shape = (red_src.height, red_src.width)

# Lade und resample die Bänder
with rasterio.open(nir_band_path) as src:
    nir = src.read(out_shape=target_shape, resampling=Resampling.bilinear).astype(float)
    nir_profile = src.profile

with rasterio.open(swir_band_path) as src:
    swir = src.read(out_shape=target_shape, resampling=Resampling.bilinear).astype(float)
    swir_profile = src.profile

with rasterio.open(swir2_band_path) as src:
    swir2 = src.read(out_shape=target_shape, resampling=Resampling.bilinear).astype(float)
    swir2_profile = src.profile

# Berechne den NDBI (für SWIR und SWIR2)
ndbi = (swir - nir) / (swir + nir)
ndbi2 = (swir2 - nir) / (swir2 + nir)

# Speichere die NDBI-Ergebnisse als GeoTIFF
ndbi_scaled = np.clip(ndbi, -1, 1) * 10000
ndbi_scaled = ndbi_scaled.astype('int16')
ndbi2_scaled = np.clip(ndbi2, -1, 1) * 10000
ndbi2_scaled = ndbi2_scaled.astype('int16')

swir_profile.update(dtype=rasterio.int16, count=1)
with rasterio.open('ndbi_output.tif', 'w', **swir_profile) as dst:
    dst.write(np.squeeze(ndbi_scaled), 1)
    print("ndbi_output.tif wurde erstellt.")

swir2_profile.update(dtype=rasterio.int16, count=1)
with rasterio.open('ndbi2_output.tif', 'w', **swir2_profile) as dst:
    dst.write(np.squeeze(ndbi2_scaled), 1)
    print("ndbi2_output.tif wurde erstellt.")

# Definiere Schwellenwerte und kommentiere die Klassen
classified_ndbi = np.zeros_like(ndbi, dtype=int)
classified_ndbi2 = np.zeros_like(ndbi2, dtype=int)

# Klasse 0: Niedrige Bebauung (Wasser und Vegetation) (NDBI < 0)
classified_ndbi[(ndbi < 0)] = 0

# Klasse 1: Moderate Bebauung (0 ≤ NDBI < 0.1)
classified_ndbi[(ndbi >= 0) & (ndbi < 0.1)] = 1

# Klasse 2: Hohe Bebauung (0.1 ≤ NDBI < 0.3)
classified_ndbi[(ndbi >= 0.1) & (ndbi < 0.3)] = 2

# Klasse 3: Sehr hohe Bebauung (NDBI ≥ 0.3)
classified_ndbi[(ndbi >= 0.3)] = 3

# Klasse 0: Vegetation (NDBI2 < -0.1)
classified_ndbi2[(ndbi2 >= -1) & (ndbi2 < -0.1)] = 0
# Klasse 1: Übergangsbereich (NDBI zwischen -0.1 und 0.1)
classified_ndbi2[(ndbi2 >= -0.1) & (ndbi2 < 0.1)] = 1
# Klasse 2: Gebautes Gebiet (NDBI > 0.1)
classified_ndbi2[(ndbi2 >= 0.1) & (ndbi2 <= 1)] = 2

# Speichere die klassifizierten NDBI-Ergebnisse als GeoTIFF
swir_profile.update(dtype=rasterio.int16, count=1)
with rasterio.open('ndbi_classified_output.tif', 'w', **swir_profile) as dst:
    dst.write(np.squeeze(classified_ndbi), 1)
    print("ndbi_classified_output.tif wurde erstellt.")

# Speichere die klassifizierten NDBI2-Ergebnisse als GeoTIFF
swir2_profile.update(dtype=rasterio.int16, count=1)
with rasterio.open('ndbi2_classified_output.tif', 'w', **swir2_profile) as dst:
    dst.write(np.squeeze(classified_ndbi2), 1)
    print("ndbi2_classified_output.tif wurde erstellt.")

# Visualisierung der klassifizierten NDBI-Ergebnisse
classified_ndbi = np.squeeze(classified_ndbi)
classified_ndbi2 = np.squeeze(classified_ndbi2)



plt = mpyplot.figure()
img = mpyplot.imshow(classified_ndbi[2000:4000,7000:9000], cmap='RdYlBu')
plt.colorbar(img)
plt.savefig("NDBI_Classified_Swir1_tmp.pdf", dpi=1200)
plt.show()



# Visualisierung des zweiten NDBI
plt2 = mpyplot.figure()
img = mpyplot.imshow(classified_ndbi2[2000:4000,7000:9000], cmap='RdYlBu')
plt2.colorbar(img)
plt2.savefig("NDBI_Swir2_tmp.pdf", dpi=1200)
plt2.show()
