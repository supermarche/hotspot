"""
NDVI-Skala: Der NDVI-Wert liegt normalerweise zwischen -1 und 1.
Werte um 0 deuten auf wenig bis keine Vegetation hin (z. B. städtische Gebiete, Wasserflächen).
Positive Werte, zwischen 0,2 und 0,5, deuten auf mäßige Vegetation hin.
Höhere Werte, nahe 1, zeigen dichte, gesunde Vegetation (z. B. Wälder).
Negative Werte, unter 0, deuten auf Wasser oder Schnee hin.
"""

import rasterio
from matplotlib.pyplot import savefig
from rasterio.enums import Resampling
import numpy as np
import rasterio.plot as plot
import matplotlib.pyplot as mpyplot
import os

import NDBI_Index as ndbi

# Pfad zu deinem .SAFE Ordner
safe_folder = 'S2B_MSIL1C_20241016T100029_N0511_R122_T33UWS_20241016T151956.SAFE/GRANULE/L1C_T33UWS_A039759_20241016T100611/IMG_DATA'

# Lade das Rot-Band (Band 4) und das NIR-Band (Band 8) als .jp2-Dateien
red_band_path = os.path.join(safe_folder, 'T33UWS_20241016T100029_B04.jp2')  # Band 4 (Rot)
nir_band_path = os.path.join(safe_folder, 'T33UWS_20241016T100029_B8A.jp2')  # Band 8 (NIR)

# Öffne das Rot-Band (10m Auflösung)
with rasterio.open(red_band_path) as red_src:
    red = red_src.read(1).astype(float)  # 2D-Array (Höhe x Breite)
    red_transform = red_src.transform
    red_profile = red_src.profile

# Öffne das NIR-Band (möglicherweise mit einer niedrigeren Auflösung)
with rasterio.open(nir_band_path) as nir_src:
    # Resample NIR auf die gleiche Auflösung wie Rot (10m)
    nir = nir_src.read(
        out_shape=(red_src.height, red_src.width),  # Neue Größe entsprechend der Rot-Band-Auflösung
        resampling=Resampling.bilinear
    ).astype(float)


# Berechne den NDVI
ndvi = (nir - red) / (nir + red)

# Skaliere den NDVI-Wert auf einen Bereich von -1 bis 1 auf int16
# wird benötigt, da von jp2 keine direkte konvertierung in tif möglich ist
ndvi_scaled = np.clip(ndvi, -1, 1) * 10000  # Multiplizieren, um den Bereich zu vergrößern
ndvi_scaled = ndvi_scaled.astype('int16')  # Konvertiere zu int16

# Speichere den NDVI als GeoTIFF
ndvi_meta = red_profile
ndvi_meta.update(dtype=rasterio.int16, count=1)

with rasterio.open('ndvi_output.tif', 'w', **ndvi_meta) as dst:
    # Überprüfe sicherheitshalber, ob das NDVI 2D ist und entferne überflüssige Dimensionen
    if ndvi_scaled.ndim == 3:
        ndvi_scaled = np.squeeze(ndvi_scaled, axis=0)

    # Schreibe das 2D-Array
    dst.write(ndvi_scaled, 1)



# Definiere NDVI-Klassen (z.B. 4 Kategorien: Wasser, kahle Flächen, mäßige Vegetation, dichte Vegetation)
ndvi_class = np.zeros_like(ndvi_scaled)
ndvi_class[ndvi_scaled < 0] = 1   # Wasser
ndvi_class[(ndvi_scaled >= 0) & (ndvi_scaled < 2000)] = 2   # Karge Flächen
ndvi_class[(ndvi_scaled >= 2000) & (ndvi_scaled < 5000)] = 3  # Mäßige Vegetation
ndvi_class[ndvi_scaled >= 5000] = 4  # Dichte Vegetation


# Visualisierung des NDVI
plt = mpyplot.figure()
img = mpyplot.imshow(ndvi_class[2000:4000,7000:9000], cmap='hot')
plt.colorbar(img)
#plt.title('NDVI-Klassifizierung')
plt.savefig("tmp.pdf", dpi=1200)
plt.show()
#plot.savefig(ndvi_scaled, cmap='RdYlGn') #RdYlGn - Ist ein Farbspektrum von rot über gelb zu grün
