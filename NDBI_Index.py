import rasterio
from rasterio.enums import Resampling
import matplotlib.pyplot as mpyplot
import os
import numpy as np

# Pfad zu deinem .SAFE Ordner
safe_folder = 'S2B_MSIL1C_20241016T100029_N0511_R122_T33UWS_20241016T151956.SAFE/GRANULE/L1C_T33UWS_A039759_20241016T100611/IMG_DATA'

# Lade das Rot-Band (Band 4) und das NIR-Band (Band 8) als .jp2-Dateien
red_band_path = os.path.join(safe_folder, 'T33UWS_20241016T100029_B04.jp2')  # Band 4 (Rot)
nir_band_path = os.path.join(safe_folder, 'T33UWS_20241016T100029_B8A.jp2')  # Band 8 (NIR)
swir_band_path = os.path.join(safe_folder, 'T33UWS_20241016T100029_B11.jp2')  # Band 11 (SWIR)
swir2_band_path = os.path.join(safe_folder, 'T33UWS_20241016T100029_B12.jp2')  # Band 12 (SWIR)

# Öffne das Rot-Band (10m Auflösung)
with rasterio.open(red_band_path) as red_src:
    red = red_src.read(1).astype(float)  # 2D-Array (Höhe x Breite)
    red_transform = red_src.transform
    red_profile = red_src.profile

# Öffne das NIR-Band und resample
with rasterio.open(nir_band_path) as nir_src:
    nir = nir_src.read(
        out_shape=(red_src.height, red_src.width),  # Neue Größe entsprechend der Rot-Band-Auflösung
        resampling=Resampling.bilinear
    ).astype(float)

# Öffne das SWIR11-Band und resample
with rasterio.open(swir_band_path) as swir_src:
    swir = swir_src.read(
        out_shape=(red_src.height, red_src.width),  # Neue Größe entsprechend der Rot-Band-Auflösung
        resampling=Resampling.bilinear
    ).astype(float)
    swir_profile = swir_src.profile  # Hier wird swir_profile definiert

 #Öffne das SWIR12-Band und resample
with rasterio.open(swir2_band_path) as swir2_src:
    swir2 = swir2_src.read(
        out_shape=(red_src.height, red_src.width),  # Neue Größe entsprechend der Rot-Band-Auflösung
        resampling=Resampling.bilinear
    ).astype(float)
    swir2_profile = swir2_src.profile  # Hier wird swir_profile definiert

# Berechne den NDBI (NDBI = (SWIR - NIR) / (SWIR + NIR))
ndbi = (swir - nir) / (swir + nir)
ndbi2 = (swir2 - nir) / (swir2 + nir)

# Skaliere den NDBI auf den Bereich von -1 bis 1, dann multipliziere mit 10000
ndbi_scaled = np.clip(ndbi, -1, 1) * 10000
ndbi_scaled = ndbi_scaled.astype('int16')  # Konvertiere zu int16

# Speichere den NDBI als GeoTIFF
ndbi_meta = swir_profile  # Verwende das Profil des SWIR-Bands für die Metadaten
ndbi_meta.update(dtype=rasterio.int16, count=1)

with rasterio.open('ndbi_output.tif', 'w', **ndbi_meta) as dst:
    if ndbi_scaled.ndim == 3:
        ndbi_scaled = np.squeeze(ndbi_scaled, axis=0)  # Sicherstellen, dass es ein 2D-Array ist

    # Schreibe das 2D-Array in die GeoTIFF-Datei
    dst.write(ndbi_scaled, 1)

print("NDBI-GeoTIFF wurde erstellt: ndbi_output.tif")

# Visualisierung (ähnlich wie für NDVI)
plt = mpyplot.figure()

# Stelle sicher, dass ndbi nur 2D ist
if ndbi.ndim > 2:
    ndbi = np.squeeze(ndbi)  # Entferne überflüssige Dimensionen

# Verwende ein Ausschnittsbereich
plt = mpyplot.figure()
img = mpyplot.imshow(ndbi)  # Verwende ein blau-rotes Farbschema für die Erkennung von bebauten Flächen
plt.colorbar(img)
plt.savefig("NDBI_tmp2.pdf", dpi=1200)
plt.show()
